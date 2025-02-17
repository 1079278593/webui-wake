#import <Foundation/Foundation.h>
@class ChatMessage;

@interface ChatSession : NSObject

@property (nonatomic, strong) NSString *sessionId;
@property (nonatomic, strong) NSString *title;
@property (nonatomic, strong) NSDate *createTime;
@property (nonatomic, strong) NSMutableArray<ChatMessage *> *messages;

+ (instancetype)sessionWithTitle:(NSString *)title;
- (void)addMessage:(ChatMessage *)message;

@end 