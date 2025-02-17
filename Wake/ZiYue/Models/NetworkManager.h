#import <Foundation/Foundation.h>
@class ServerConnection;

typedef void(^MessageCompletionBlock)(NSDictionary *response, NSError *error);

@interface NetworkManager : NSObject

@property (nonatomic, strong, readonly) ServerConnection *currentConnection;
@property (nonatomic, assign, readonly) BOOL isConnected;

+ (instancetype)sharedManager;

- (void)connectToServer:(ServerConnection *)connection completion:(void(^)(BOOL success, NSError *error))completion;
- (void)disconnectWithCompletion:(void(^)(void))completion;
- (void)sendMessage:(NSString *)message completion:(MessageCompletionBlock)completion;
- (void)sendStreamMessage:(NSString *)message 
              onProgress:(void(^)(NSString *partialResponse))progressBlock
              completion:(MessageCompletionBlock)completion;

@end 