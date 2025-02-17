#import <UIKit/UIKit.h>
@class ChatMessage;

@interface ChatMessageCell : UITableViewCell

@property (nonatomic, strong) UILabel *messageLabel;
@property (nonatomic, strong) UIButton *playVoiceButton;
@property (nonatomic, strong) UIView *bubbleView;

- (void)configureCellWithMessage:(ChatMessage *)message;

@end 