#import "ChatMessage.h"

@implementation ChatMessage

+ (instancetype)messageWithContent:(NSString *)content type:(MessageType)type isFromUser:(BOOL)isFromUser {
    ChatMessage *message = [[ChatMessage alloc] init];
    message.messageId = [[NSUUID UUID] UUIDString];
    message.content = content;
    message.type = type;
    message.isFromUser = isFromUser;
    message.timestamp = [NSDate date];
    return message;
}

#pragma mark - NSCoding

- (void)encodeWithCoder:(NSCoder *)coder {
    [coder encodeObject:self.messageId forKey:@"messageId"];
    [coder encodeObject:self.content forKey:@"content"];
    [coder encodeInteger:self.type forKey:@"type"];
    [coder encodeBool:self.isFromUser forKey:@"isFromUser"];
    [coder encodeObject:self.timestamp forKey:@"timestamp"];
    [coder encodeObject:self.voiceUrl forKey:@"voiceUrl"];
}

- (instancetype)initWithCoder:(NSCoder *)coder {
    self = [super init];
    if (self) {
        _messageId = [coder decodeObjectForKey:@"messageId"];
        _content = [coder decodeObjectForKey:@"content"];
        _type = [coder decodeIntegerForKey:@"type"];
        _isFromUser = [coder decodeBoolForKey:@"isFromUser"];
        _timestamp = [coder decodeObjectForKey:@"timestamp"];
        _voiceUrl = [coder decodeObjectForKey:@"voiceUrl"];
    }
    return self;
}

@end 