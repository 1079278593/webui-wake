//
//  ViewController.h
//  ZiYue
//
//  Created by imvt on 2025/2/17.
//

#import <UIKit/UIKit.h>
@class ChatSession;
@class ServerConnection;

@interface ViewController : UIViewController

@property (nonatomic, strong) ChatSession *currentSession;
@property (nonatomic, strong) ServerConnection *currentConnection;
@property (nonatomic, strong) NSMutableArray<ChatSession *> *sessions;
@property (nonatomic, strong) NSMutableArray<ServerConnection *> *connections;

// UI Elements
@property (nonatomic, strong) UITableView *chatTableView;
@property (nonatomic, strong) UITextField *messageInputField;
@property (nonatomic, strong) UIButton *sendButton;
@property (nonatomic, strong) UIButton *voiceInputButton;
@property (nonatomic, strong) UIButton *realTimeVoiceButton;
@property (nonatomic, strong) UIButton *sessionsButton;
@property (nonatomic, strong) UIButton *connectionsButton;

// Actions
- (void)showSessionsList;
- (void)showConnectionsList;
- (void)showNewConnectionDialog;
- (void)startVoiceInput;
- (void)startRealTimeVoice;
- (void)sendMessage;

@end

