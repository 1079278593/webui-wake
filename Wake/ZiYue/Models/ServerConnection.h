#import <Foundation/Foundation.h>

@interface ServerConnection : NSObject

@property (nonatomic, strong) NSString *connectionId;
@property (nonatomic, strong) NSString *serverUrl;
@property (nonatomic, strong) NSDate *lastConnectedTime;
@property (nonatomic, assign) BOOL isConnected;

+ (instancetype)connectionWithUrl:(NSString *)url;
- (void)connectWithCompletion:(void(^)(BOOL success, NSError *error))completion;
- (void)disconnect;

@end 