#import "ChatMessageCell.h"
#import "ChatMessage.h"

@implementation ChatMessageCell

- (instancetype)initWithStyle:(UITableViewCellStyle)style reuseIdentifier:(NSString *)reuseIdentifier {
    self = [super initWithStyle:style reuseIdentifier:reuseIdentifier];
    if (self) {
        [self setupUI];
    }
    return self;
}

- (void)setupUI {
    self.selectionStyle = UITableViewCellSelectionStyleNone;
    
    // 气泡视图
    self.bubbleView = [[UIView alloc] init];
    self.bubbleView.layer.cornerRadius = 12;
    self.bubbleView.clipsToBounds = YES;
    [self.contentView addSubview:self.bubbleView];
    
    // 消息文本标签
    self.messageLabel = [[UILabel alloc] init];
    self.messageLabel.numberOfLines = 0;
    self.messageLabel.font = [UIFont systemFontOfSize:16];
    [self.bubbleView addSubview:self.messageLabel];
    
    // 语音播放按钮
    self.playVoiceButton = [UIButton buttonWithType:UIButtonTypeSystem];
    [self.playVoiceButton setImage:[UIImage systemImageNamed:@"play.fill"] forState:UIControlStateNormal];
    self.playVoiceButton.hidden = YES;
    [self.bubbleView addSubview:self.playVoiceButton];
    
    // 设置自动布局
    [self setupConstraints];
}

- (void)setupConstraints {
    self.bubbleView.translatesAutoresizingMaskIntoConstraints = NO;
    self.messageLabel.translatesAutoresizingMaskIntoConstraints = NO;
    self.playVoiceButton.translatesAutoresizingMaskIntoConstraints = NO;
    
    [NSLayoutConstraint activateConstraints:@[
        [self.bubbleView.topAnchor constraintEqualToAnchor:self.contentView.topAnchor constant:8],
        [self.bubbleView.bottomAnchor constraintEqualToAnchor:self.contentView.bottomAnchor constant:-8],
        [self.bubbleView.widthAnchor constraintLessThanOrEqualToConstant:280],
        
        [self.messageLabel.topAnchor constraintEqualToAnchor:self.bubbleView.topAnchor constant:8],
        [self.messageLabel.leadingAnchor constraintEqualToAnchor:self.bubbleView.leadingAnchor constant:12],
        [self.messageLabel.trailingAnchor constraintEqualToAnchor:self.bubbleView.trailingAnchor constant:-12],
        [self.messageLabel.bottomAnchor constraintEqualToAnchor:self.bubbleView.bottomAnchor constant:-8],
        
        [self.playVoiceButton.centerYAnchor constraintEqualToAnchor:self.bubbleView.centerYAnchor],
        [self.playVoiceButton.leadingAnchor constraintEqualToAnchor:self.bubbleView.leadingAnchor constant:12],
        [self.playVoiceButton.widthAnchor constraintEqualToConstant:30],
        [self.playVoiceButton.heightAnchor constraintEqualToConstant:30]
    ]];
}

- (void)configureCellWithMessage:(ChatMessage *)message {
    // 设置消息内容
    self.messageLabel.text = message.content;
    
    // 根据消息类型显示/隐藏语音播放按钮
    self.playVoiceButton.hidden = (message.type != MessageTypeVoice);
    
    // 设置布局方向和颜色
    if (message.isFromUser) {
        self.bubbleView.backgroundColor = [UIColor systemBlueColor];
        self.messageLabel.textColor = [UIColor whiteColor];
        [self.bubbleView.leadingAnchor constraintEqualToAnchor:self.contentView.leadingAnchor constant:16].active = NO;
        [self.bubbleView.trailingAnchor constraintEqualToAnchor:self.contentView.trailingAnchor constant:-16].active = YES;
    } else {
        self.bubbleView.backgroundColor = [UIColor systemGrayColor];
        self.messageLabel.textColor = [UIColor whiteColor];
        [self.bubbleView.leadingAnchor constraintEqualToAnchor:self.contentView.leadingAnchor constant:16].active = YES;
        [self.bubbleView.trailingAnchor constraintEqualToAnchor:self.contentView.trailingAnchor constant:-16].active = NO;
    }
}

@end 