#import "ServerConnection.h"
#import "NetworkManager.h"

@implementation ServerConnection

+ (instancetype)connectionWithUrl:(NSString *)url {
    ServerConnection *connection = [[ServerConnection alloc] init];
    connection.serverUrl = url;
    connection.connectionId = [[NSUUID UUID] UUIDString];
    connection.lastConnectedTime = [NSDate date];
    return connection;
}

- (void)connectWithCompletion:(void(^)(BOOL success, NSError *error))completion {
    [[NetworkManager sharedManager] connectToServer:self completion:^(BOOL success, NSError *error) {
        self.isConnected = success;
        if (success) {
            self.lastConnectedTime = [NSDate date];
        }
        if (completion) {
            completion(success, error);
        }
    }];
}

- (void)disconnect {
    [[NetworkManager sharedManager] disconnectWithCompletion:^{
        self.isConnected = NO;
    }];
}

#pragma mark - NSCoding

- (void)encodeWithCoder:(NSCoder *)coder {
    [coder encodeObject:self.connectionId forKey:@"connectionId"];
    [coder encodeObject:self.serverUrl forKey:@"serverUrl"];
    [coder encodeObject:self.lastConnectedTime forKey:@"lastConnectedTime"];
}

- (instancetype)initWithCoder:(NSCoder *)coder {
    self = [super init];
    if (self) {
        _connectionId = [coder decodeObjectForKey:@"connectionId"];
        _serverUrl = [coder decodeObjectForKey:@"serverUrl"];
        _lastConnectedTime = [coder decodeObjectForKey:@"lastConnectedTime"];
    }
    return self;
}

@end 