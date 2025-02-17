#import <Foundation/Foundation.h>

typedef NS_ENUM(NSInteger, MessageType) {
    MessageTypeText,
    MessageTypeVoice
};

@interface ChatMessage : NSObject

@property (nonatomic, strong) NSString *messageId;
@property (nonatomic, strong) NSString *content;
@property (nonatomic, assign) MessageType type;
@property (nonatomic, assign) BOOL isFromUser;
@property (nonatomic, strong) NSDate *timestamp;
@property (nonatomic, strong) NSString *voiceUrl;

+ (instancetype)messageWithContent:(NSString *)content type:(MessageType)type isFromUser:(BOOL)isFromUser;

@end 