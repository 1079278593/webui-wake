#import "ChatSession.h"
#import "ChatMessage.h"

@implementation ChatSession

+ (instancetype)sessionWithTitle:(NSString *)title {
    ChatSession *session = [[ChatSession alloc] init];
    session.sessionId = [[NSUUID UUID] UUIDString];
    session.title = title;
    session.createTime = [NSDate date];
    session.messages = [NSMutableArray array];
    return session;
}

- (void)addMessage:(ChatMessage *)message {
    if (!self.messages) {
        self.messages = [NSMutableArray array];
    }
    [self.messages addObject:message];
}

#pragma mark - NSCoding

- (void)encodeWithCoder:(NSCoder *)coder {
    [coder encodeObject:self.sessionId forKey:@"sessionId"];
    [coder encodeObject:self.title forKey:@"title"];
    [coder encodeObject:self.createTime forKey:@"createTime"];
    [coder encodeObject:self.messages forKey:@"messages"];
}

- (instancetype)initWithCoder:(NSCoder *)coder {
    self = [super init];
    if (self) {
        _sessionId = [coder decodeObjectForKey:@"sessionId"];
        _title = [coder decodeObjectForKey:@"title"];
        _createTime = [coder decodeObjectForKey:@"createTime"];
        _messages = [coder decodeObjectForKey:@"messages"];
    }
    return self;
}

@end 