#import "NetworkManager.h"
#import "ServerConnection.h"
#import "SocketRocket.h"

@interface NetworkManager () <SRWebSocketDelegate>

@property (nonatomic, strong) SRWebSocket *webSocket;
@property (nonatomic, strong) ServerConnection *currentConnection;
@property (nonatomic, assign) BOOL isConnected;
@property (nonatomic, strong) NSMutableDictionary *pendingRequests;
@property (nonatomic, copy) void(^connectionCompletion)(BOOL success, NSError *error);
@property (nonatomic, copy) void(^currentProgressBlock)(NSString *partialResponse);
@property (nonatomic, copy) MessageCompletionBlock currentCompletion;

@end

@implementation NetworkManager

+ (instancetype)sharedManager {
    static NetworkManager *sharedManager = nil;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        sharedManager = [[NetworkManager alloc] init];
    });
    return sharedManager;
}

- (instancetype)init {
    self = [super init];
    if (self) {
        _pendingRequests = [NSMutableDictionary dictionary];
    }
    return self;
}

#pragma mark - Public Methods

- (void)connectToServer:(ServerConnection *)connection completion:(void(^)(BOOL success, NSError *error))completion {
    if (self.webSocket) {
        [self.webSocket close];
        self.webSocket = nil;
    }
    
    self.currentConnection = connection;
    self.connectionCompletion = completion;
    
    NSURL *url = [NSURL URLWithString:connection.serverUrl];
    self.webSocket = [[SRWebSocket alloc] initWithURL:url];
    self.webSocket.delegate = self;
    [self.webSocket open];
}

- (void)disconnectWithCompletion:(void(^)(void))completion {
    [self.webSocket close];
    self.webSocket = nil;
    self.isConnected = NO;
    self.currentConnection = nil;
    if (completion) {
        completion();
    }
}

- (void)sendMessage:(NSString *)message completion:(MessageCompletionBlock)completion {
    if (!self.isConnected) {
        if (completion) {
            NSError *error = [NSError errorWithDomain:@"com.kongfuzi.network" code:-1 userInfo:@{NSLocalizedDescriptionKey: @"Not connected to server"}];
            completion(nil, error);
        }
        return;
    }
    
    NSDictionary *request = @{
        @"model": @"deepseek",
        @"prompt": message,
        @"stream": @NO
    };
    
    NSError *error;
    NSData *jsonData = [NSJSONSerialization dataWithJSONObject:request options:0 error:&error];
    if (error) {
        if (completion) {
            completion(nil, error);
        }
        return;
    }
    
    NSString *jsonString = [[NSString alloc] initWithData:jsonData encoding:NSUTF8StringEncoding];
    [self.webSocket send:jsonString];
    self.currentCompletion = completion;
}

- (void)sendStreamMessage:(NSString *)message 
              onProgress:(void(^)(NSString *partialResponse))progressBlock
              completion:(MessageCompletionBlock)completion {
    if (!self.isConnected) {
        if (completion) {
            NSError *error = [NSError errorWithDomain:@"com.kongfuzi.network" code:-1 userInfo:@{NSLocalizedDescriptionKey: @"Not connected to server"}];
            completion(nil, error);
        }
        return;
    }
    
    NSDictionary *request = @{
        @"model": @"deepseek",
        @"prompt": message,
        @"stream": @YES
    };
    
    NSError *error;
    NSData *jsonData = [NSJSONSerialization dataWithJSONObject:request options:0 error:&error];
    if (error) {
        if (completion) {
            completion(nil, error);
        }
        return;
    }
    
    NSString *jsonString = [[NSString alloc] initWithData:jsonData encoding:NSUTF8StringEncoding];
    [self.webSocket send:jsonString];
    self.currentProgressBlock = progressBlock;
    self.currentCompletion = completion;
}

#pragma mark - SRWebSocketDelegate

- (void)webSocket:(SRWebSocket *)webSocket didReceiveMessage:(id)message {
    NSData *jsonData = [message dataUsingEncoding:NSUTF8StringEncoding];
    NSError *error;
    NSDictionary *response = [NSJSONSerialization JSONObjectWithData:jsonData options:0 error:&error];
    
    if (error) {
        if (self.currentCompletion) {
            self.currentCompletion(nil, error);
        }
        return;
    }
    
    if ([response[@"done"] boolValue]) {
        if (self.currentCompletion) {
            self.currentCompletion(response, nil);
            self.currentCompletion = nil;
            self.currentProgressBlock = nil;
        }
    } else {
        if (self.currentProgressBlock) {
            NSString *partialResponse = response[@"response"];
            self.currentProgressBlock(partialResponse);
        }
    }
}

- (void)webSocketDidOpen:(SRWebSocket *)webSocket {
    self.isConnected = YES;
    if (self.connectionCompletion) {
        self.connectionCompletion(YES, nil);
        self.connectionCompletion = nil;
    }
}

- (void)webSocket:(SRWebSocket *)webSocket didFailWithError:(NSError *)error {
    self.isConnected = NO;
    if (self.connectionCompletion) {
        self.connectionCompletion(NO, error);
        self.connectionCompletion = nil;
    }
    
    if (self.currentCompletion) {
        self.currentCompletion(nil, error);
        self.currentCompletion = nil;
        self.currentProgressBlock = nil;
    }
}

- (void)webSocket:(SRWebSocket *)webSocket didCloseWithCode:(NSInteger)code reason:(NSString *)reason wasClean:(BOOL)wasClean {
    self.isConnected = NO;
    if (self.connectionCompletion) {
        NSError *error = [NSError errorWithDomain:@"com.kongfuzi.network" code:code userInfo:@{NSLocalizedDescriptionKey: reason ?: @"Connection closed"}];
        self.connectionCompletion(NO, error);
        self.connectionCompletion = nil;
    }
}

@end 
