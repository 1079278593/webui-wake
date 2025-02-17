//
//  ViewController.m
//  ZiYue
//
//  Created by imvt on 2025/2/17.
//

#import "ViewController.h"
#import "ChatSession.h"
#import "ChatMessage.h"
#import "ServerConnection.h"
#import "NetworkManager.h"
#import "ChatMessageCell.h"
#import "VoiceManager.h"

@interface ViewController () <UITableViewDelegate, UITableViewDataSource, UITextFieldDelegate>
@property (nonatomic, strong) UIActivityIndicatorView *voiceIndicator;
@property (nonatomic, strong) UILabel *voiceHintLabel;
@end

@implementation ViewController

- (void)viewDidLoad {
    [super viewDidLoad];
    [self setupUI];
    [self loadSavedData];
}

- (void)setupUI {
    // 设置导航栏
    self.title = @"孔夫子";
    self.navigationItem.rightBarButtonItem = [[UIBarButtonItem alloc] initWithImage:[UIImage systemImageNamed:@"gear"] style:UIBarButtonItemStylePlain target:self action:@selector(showConnectionsList)];
    
    // 聊天列表
    self.chatTableView = [[UITableView alloc] initWithFrame:CGRectZero style:UITableViewStylePlain];
    self.chatTableView.delegate = self;
    self.chatTableView.dataSource = self;
    [self.view addSubview:self.chatTableView];
    
    // 底部输入区域
    UIView *inputView = [[UIView alloc] init];
    inputView.backgroundColor = [UIColor systemBackgroundColor];
    [self.view addSubview:inputView];
    
    // 文本输入框
    self.messageInputField = [[UITextField alloc] init];
    self.messageInputField.placeholder = @"输入消息...";
    self.messageInputField.delegate = self;
    [inputView addSubview:self.messageInputField];
    
    // 发送按钮
    self.sendButton = [UIButton buttonWithType:UIButtonTypeSystem];
    [self.sendButton setTitle:@"发送" forState:UIControlStateNormal];
    [self.sendButton addTarget:self action:@selector(sendMessage) forControlEvents:UIControlEventTouchUpInside];
    [inputView addSubview:self.sendButton];
    
    // 语音输入按钮
    self.voiceInputButton = [UIButton buttonWithType:UIButtonTypeSystem];
    [self.voiceInputButton setImage:[UIImage systemImageNamed:@"mic"] forState:UIControlStateNormal];
    [self.voiceInputButton addTarget:self action:@selector(startVoiceInput) forControlEvents:UIControlEventTouchUpInside];
    [inputView addSubview:self.voiceInputButton];
    
    // 实时语音按钮
    self.realTimeVoiceButton = [UIButton buttonWithType:UIButtonTypeSystem];
    [self.realTimeVoiceButton setImage:[UIImage systemImageNamed:@"mic.circle"] forState:UIControlStateNormal];
    [self.realTimeVoiceButton addTarget:self action:@selector(startRealTimeVoice) forControlEvents:UIControlEventTouchUpInside];
    [inputView addSubview:self.realTimeVoiceButton];
    
    // 添加语音提示UI
    self.voiceIndicator = [[UIActivityIndicatorView alloc] initWithActivityIndicatorStyle:UIActivityIndicatorViewStyleMedium];
    self.voiceIndicator.hidden = YES;
    [self.view addSubview:self.voiceIndicator];
    
    self.voiceHintLabel = [[UILabel alloc] init];
    self.voiceHintLabel.textAlignment = NSTextAlignmentCenter;
    self.voiceHintLabel.font = [UIFont systemFontOfSize:14];
    self.voiceHintLabel.textColor = [UIColor grayColor];
    self.voiceHintLabel.hidden = YES;
    [self.view addSubview:self.voiceHintLabel];
    
    // 设置自动布局约束
    [self setupConstraints];
    
    // 设置语音按钮的长按手势
    UILongPressGestureRecognizer *voiceLongPress = [[UILongPressGestureRecognizer alloc]
                                                    initWithTarget:self
                                                    action:@selector(handleVoiceLongPress:)];
    [self.voiceInputButton addGestureRecognizer:voiceLongPress];
    
    // 设置实时语音按钮的长按手势
    UILongPressGestureRecognizer *realtimeVoiceLongPress = [[UILongPressGestureRecognizer alloc]
                                                            initWithTarget:self
                                                            action:@selector(handleRealtimeVoiceLongPress:)];
    [self.realTimeVoiceButton addGestureRecognizer:realtimeVoiceLongPress];
}

- (void)setupConstraints {
    self.chatTableView.translatesAutoresizingMaskIntoConstraints = NO;
    [NSLayoutConstraint activateConstraints:@[
        [self.chatTableView.topAnchor constraintEqualToAnchor:self.view.safeAreaLayoutGuide.topAnchor],
        [self.chatTableView.leadingAnchor constraintEqualToAnchor:self.view.leadingAnchor],
        [self.chatTableView.trailingAnchor constraintEqualToAnchor:self.view.trailingAnchor],
        [self.chatTableView.bottomAnchor constraintEqualToAnchor:self.view.bottomAnchor constant:-60]
    ]];
    
    // 添加语音UI的约束
    self.voiceIndicator.translatesAutoresizingMaskIntoConstraints = NO;
    self.voiceHintLabel.translatesAutoresizingMaskIntoConstraints = NO;
    
    [NSLayoutConstraint activateConstraints:@[
        [self.voiceIndicator.centerXAnchor constraintEqualToAnchor:self.view.centerXAnchor],
        [self.voiceIndicator.centerYAnchor constraintEqualToAnchor:self.view.centerYAnchor],
        
        [self.voiceHintLabel.topAnchor constraintEqualToAnchor:self.voiceIndicator.bottomAnchor constant:8],
        [self.voiceHintLabel.centerXAnchor constraintEqualToAnchor:self.view.centerXAnchor],
        [self.voiceHintLabel.widthAnchor constraintEqualToConstant:200],
        [self.voiceHintLabel.heightAnchor constraintEqualToConstant:20]
    ]];
}

#pragma mark - Actions

- (void)sendMessage {
    NSString *text = self.messageInputField.text;
    if (text.length == 0) return;
    
    // 创建并添加用户消息
    ChatMessage *userMessage = [ChatMessage messageWithContent:text type:MessageTypeText isFromUser:YES];
    [self.currentSession addMessage:userMessage];
    [self.chatTableView reloadData];
    self.messageInputField.text = @"";
    
    // 发送到服务器
    [[NetworkManager sharedManager] sendStreamMessage:text onProgress:^(NSString *partialResponse) {
        // 更新AI回复的最后一条消息
        ChatMessage *aiMessage = [self.currentSession.messages lastObject];
        if (!aiMessage || aiMessage.isFromUser) {
            aiMessage = [ChatMessage messageWithContent:partialResponse type:MessageTypeText isFromUser:NO];
            [self.currentSession addMessage:aiMessage];
        } else {
            aiMessage.content = [aiMessage.content stringByAppendingString:partialResponse];
        }
        [self.chatTableView reloadData];
        
        // 滚动到底部
        NSIndexPath *lastIndexPath = [NSIndexPath indexPathForRow:self.currentSession.messages.count - 1 inSection:0];
        [self.chatTableView scrollToRowAtIndexPath:lastIndexPath atScrollPosition:UITableViewScrollPositionBottom animated:YES];
    } completion:^(NSDictionary *response, NSError *error) {
        if (error) {
            // 显示错误提示
            UIAlertController *alert = [UIAlertController alertControllerWithTitle:@"错误"
                                                                         message:error.localizedDescription
                                                                  preferredStyle:UIAlertControllerStyleAlert];
            [alert addAction:[UIAlertAction actionWithTitle:@"确定" style:UIAlertActionStyleDefault handler:nil]];
            [self presentViewController:alert animated:YES completion:nil];
        }
    }];
}

#pragma mark - Voice Actions

- (void)handleVoiceLongPress:(UILongPressGestureRecognizer *)gesture {
    if (gesture.state == UIGestureRecognizerStateBegan) {
        [self startVoiceInput];
    } else if (gesture.state == UIGestureRecognizerStateEnded ||
               gesture.state == UIGestureRecognizerStateCancelled) {
        [self stopVoiceInput];
    }
}

- (void)handleRealtimeVoiceLongPress:(UILongPressGestureRecognizer *)gesture {
    if (gesture.state == UIGestureRecognizerStateBegan) {
        [self startRealTimeVoice];
    } else if (gesture.state == UIGestureRecognizerStateEnded ||
               gesture.state == UIGestureRecognizerStateCancelled) {
        [self stopRealTimeVoice];
    }
}

- (void)startVoiceInput {
    // 检查权限
    [[VoiceManager sharedManager] requestPermissionWithCompletion:^(BOOL granted) {
        if (!granted) {
            [self showAlert:@"需要麦克风和语音识别权限" message:@"请在设置中开启相关权限"];
            return;
        }
        
        // 显示录音提示
        self.voiceHintLabel.text = @"正在录音...";
        self.voiceHintLabel.hidden = NO;
        [self.voiceIndicator startAnimating];
        self.voiceIndicator.hidden = NO;
        
        // 开始录音
        [[VoiceManager sharedManager] startRecordingWithCompletion:^(NSString *recognizedText,
                                                                    NSString *audioPath,
                                                                    NSError *error) {
            // 隐藏录音提示
            self.voiceHintLabel.hidden = YES;
            [self.voiceIndicator stopAnimating];
            self.voiceIndicator.hidden = YES;
            
            if (error) {
                [self showAlert:@"录音失败" message:error.localizedDescription];
                return;
            }
            
            // 创建语音消息
            ChatMessage *message = [ChatMessage messageWithContent:recognizedText
                                                           type:MessageTypeVoice
                                                     isFromUser:YES];
            message.voiceUrl = audioPath;
            [self.currentSession addMessage:message];
            [self.chatTableView reloadData];
            
            // 发送消息到服务器
            [[NetworkManager sharedManager] sendStreamMessage:recognizedText
                                                 onProgress:^(NSString *partialResponse) {
                // 更新AI回复
                ChatMessage *aiMessage = [self.currentSession.messages lastObject];
                if (!aiMessage || aiMessage.isFromUser) {
                    aiMessage = [ChatMessage messageWithContent:partialResponse
                                                         type:MessageTypeText
                                                   isFromUser:NO];
                    [self.currentSession addMessage:aiMessage];
                } else {
                    aiMessage.content = [aiMessage.content stringByAppendingString:partialResponse];
                }
                [self.chatTableView reloadData];
                
                // 滚动到底部
                [self scrollToBottom];
            } completion:^(NSDictionary *response, NSError *error) {
                if (error) {
                    [self showAlert:@"发送失败" message:error.localizedDescription];
                }
            }];
        }];
    }];
}

- (void)stopVoiceInput {
    [[VoiceManager sharedManager] stopRecording];
}

- (void)startRealTimeVoice {
    // 检查权限
    [[VoiceManager sharedManager] requestPermissionWithCompletion:^(BOOL granted) {
        if (!granted) {
            [self showAlert:@"需要麦克风和语音识别权限" message:@"请在设置中开启相关权限"];
            return;
        }
        
        // 显示录音提示
        self.voiceHintLabel.text = @"正在实时对话...";
        self.voiceHintLabel.hidden = NO;
        [self.voiceIndicator startAnimating];
        self.voiceIndicator.hidden = NO;
        
        // 开始实时语音识别
        [[VoiceManager sharedManager] startRealtimeRecordingWithBlock:^(NSString *partialText) {
            // 更新用户消息
            ChatMessage *userMessage = [self.currentSession.messages lastObject];
            if (!userMessage || !userMessage.isFromUser) {
                userMessage = [ChatMessage messageWithContent:partialText
                                                      type:MessageTypeText
                                                isFromUser:YES];
                [self.currentSession addMessage:userMessage];
            } else {
                userMessage.content = partialText;
            }
            [self.chatTableView reloadData];
            [self scrollToBottom];
            
        } completion:^(NSString *finalText, NSError *error) {
            if (error) {
                [self showAlert:@"语音识别失败" message:error.localizedDescription];
                return;
            }
            
            // 发送最终识别结果到服务器
            [[NetworkManager sharedManager] sendStreamMessage:finalText
                                                 onProgress:^(NSString *partialResponse) {
                // 更新AI回复
                ChatMessage *aiMessage = [self.currentSession.messages lastObject];
                if (!aiMessage || aiMessage.isFromUser) {
                    aiMessage = [ChatMessage messageWithContent:partialResponse
                                                         type:MessageTypeText
                                                   isFromUser:NO];
                    [self.currentSession addMessage:aiMessage];
                } else {
                    aiMessage.content = [aiMessage.content stringByAppendingString:partialResponse];
                }
                [self.chatTableView reloadData];
                [self scrollToBottom];
                
            } completion:^(NSDictionary *response, NSError *error) {
                if (error) {
                    [self showAlert:@"发送失败" message:error.localizedDescription];
                }
            }];
        }];
    }];
}

- (void)stopRealTimeVoice {
    [[VoiceManager sharedManager] stopRealtimeRecording];
    self.voiceHintLabel.hidden = YES;
    [self.voiceIndicator stopAnimating];
    self.voiceIndicator.hidden = YES;
}

#pragma mark - Helper Methods

- (void)showAlert:(NSString *)title message:(NSString *)message {
    UIAlertController *alert = [UIAlertController alertControllerWithTitle:title
                                                                 message:message
                                                          preferredStyle:UIAlertControllerStyleAlert];
    [alert addAction:[UIAlertAction actionWithTitle:@"确定" style:UIAlertActionStyleDefault handler:nil]];
    [self presentViewController:alert animated:YES completion:nil];
}

- (void)scrollToBottom {
    NSIndexPath *lastIndexPath = [NSIndexPath indexPathForRow:self.currentSession.messages.count - 1
                                                   inSection:0];
    [self.chatTableView scrollToRowAtIndexPath:lastIndexPath
                             atScrollPosition:UITableViewScrollPositionBottom
                                   animated:YES];
}

- (void)showSessionsList {
    // TODO: 显示会话列表
}

- (void)showConnectionsList {
    UIAlertController *alert = [UIAlertController alertControllerWithTitle:@"服务器连接"
                                                                 message:nil
                                                          preferredStyle:UIAlertControllerStyleActionSheet];
    
    // 添加已保存的连接
    for (ServerConnection *connection in self.connections) {
        NSString *title = [NSString stringWithFormat:@"%@ (%@)",
                          connection.serverUrl,
                          connection.isConnected ? @"已连接" : @"未连接"];
        
        UIAlertAction *action = [UIAlertAction actionWithTitle:title
                                                        style:UIAlertActionStyleDefault
                                                      handler:^(UIAlertAction *action) {
            [self connectToServer:connection];
        }];
        [alert addAction:action];
    }
    
    // 添加新连接选项
    [alert addAction:[UIAlertAction actionWithTitle:@"新建连接"
                                            style:UIAlertActionStyleDefault
                                          handler:^(UIAlertAction *action) {
        [self showNewConnectionDialog];
    }]];
    
    // 添加取消选项
    [alert addAction:[UIAlertAction actionWithTitle:@"取消"
                                            style:UIAlertActionStyleCancel
                                          handler:nil]];
    
    [self presentViewController:alert animated:YES completion:nil];
}

- (void)showNewConnectionDialog {
    UIAlertController *alert = [UIAlertController alertControllerWithTitle:@"新建连接"
                                                                 message:@"请输入服务器URL"
                                                          preferredStyle:UIAlertControllerStyleAlert];
    
    [alert addTextFieldWithConfigurationHandler:^(UITextField *textField) {
        textField.placeholder = @"http://localhost:11434";
    }];
    
    UIAlertAction *cancelAction = [UIAlertAction actionWithTitle:@"取消"
                                                          style:UIAlertActionStyleCancel
                                                        handler:nil];
    
    UIAlertAction *confirmAction = [UIAlertAction actionWithTitle:@"确定"
                                                           style:UIAlertActionStyleDefault
                                                         handler:^(UIAlertAction *action) {
        NSString *url = alert.textFields.firstObject.text;
        ServerConnection *connection = [ServerConnection connectionWithUrl:url];
        [self.connections addObject:connection];
        [self connectToServer:connection];
        [self saveConnections];
    }];
    
    [alert addAction:cancelAction];
    [alert addAction:confirmAction];
    [self presentViewController:alert animated:YES completion:nil];
}

#pragma mark - Private Methods

- (void)connectToServer:(ServerConnection *)connection {
    [connection connectWithCompletion:^(BOOL success, NSError *error) {
        if (success) {
            self.currentConnection = connection;
            [self saveConnections];
        } else {
            UIAlertController *alert = [UIAlertController alertControllerWithTitle:@"连接失败"
                                                                         message:error.localizedDescription
                                                                  preferredStyle:UIAlertControllerStyleAlert];
            [alert addAction:[UIAlertAction actionWithTitle:@"确定" style:UIAlertActionStyleDefault handler:nil]];
            [self presentViewController:alert animated:YES completion:nil];
        }
    }];
}

- (void)saveConnections {
    NSArray *paths = NSSearchPathForDirectoriesInDomains(NSDocumentDirectory, NSUserDomainMask, YES);
    NSString *documentsDirectory = [paths firstObject];
    NSString *path = [documentsDirectory stringByAppendingPathComponent:@"connections.data"];
    
    [NSKeyedArchiver archiveRootObject:self.connections toFile:path];
}

- (void)loadSavedData {
    // 加载保存的连接
    NSArray *paths = NSSearchPathForDirectoriesInDomains(NSDocumentDirectory, NSUserDomainMask, YES);
    NSString *documentsDirectory = [paths firstObject];
    NSString *path = [documentsDirectory stringByAppendingPathComponent:@"connections.data"];
    
    NSArray *savedConnections = [NSKeyedUnarchiver unarchiveObjectWithFile:path];
    self.connections = savedConnections ? [savedConnections mutableCopy] : [NSMutableArray array];
    
    // 创建新会话
    self.sessions = [NSMutableArray array];
    self.currentSession = [ChatSession sessionWithTitle:@"新会话"];
    [self.sessions addObject:self.currentSession];
}

#pragma mark - UITableViewDataSource

- (NSInteger)tableView:(UITableView *)tableView numberOfRowsInSection:(NSInteger)section {
    return self.currentSession.messages.count;
}

- (UITableViewCell *)tableView:(UITableView *)tableView cellForRowAtIndexPath:(NSIndexPath *)indexPath {
    static NSString *cellIdentifier = @"ChatMessageCell";
    
    ChatMessageCell *cell = [tableView dequeueReusableCellWithIdentifier:cellIdentifier];
    if (!cell) {
        cell = [[ChatMessageCell alloc] initWithStyle:UITableViewCellStyleDefault reuseIdentifier:cellIdentifier];
    }
    
    ChatMessage *message = self.currentSession.messages[indexPath.row];
    [cell configureCellWithMessage:message];
    
    return cell;
}

@end

