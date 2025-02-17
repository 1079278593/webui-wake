#import "VoiceManager.h"

@interface VoiceManager () <SFSpeechRecognizerDelegate, AVAudioRecorderDelegate>

@property (nonatomic, strong) SFSpeechRecognizer *speechRecognizer;
@property (nonatomic, strong) SFSpeechAudioBufferRecognitionRequest *recognitionRequest;
@property (nonatomic, strong) SFSpeechRecognitionTask *recognitionTask;
@property (nonatomic, strong) AVAudioEngine *audioEngine;
@property (nonatomic, strong) AVAudioRecorder *audioRecorder;
@property (nonatomic, strong) AVAudioPlayer *audioPlayer;

@property (nonatomic, assign) VoiceRecordingState state;
@property (nonatomic, assign) BOOL isRealTimeMode;
@property (nonatomic, copy) void(^recordingCompletion)(NSString *recognizedText, NSString *audioPath, NSError *error);
@property (nonatomic, copy) void(^realtimePartialBlock)(NSString *partialText);
@property (nonatomic, copy) void(^realtimeCompletion)(NSString *finalText, NSError *error);

@end

@implementation VoiceManager

+ (instancetype)sharedManager {
    static VoiceManager *sharedManager = nil;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        sharedManager = [[VoiceManager alloc] init];
    });
    return sharedManager;
}

- (instancetype)init {
    self = [super init];
    if (self) {
        _state = VoiceRecordingStateIdle;
        _speechRecognizer = [[SFSpeechRecognizer alloc] initWithLocale:[NSLocale localeWithLocaleIdentifier:@"zh-CN"]];
        _speechRecognizer.delegate = self;
        _audioEngine = [[AVAudioEngine alloc] init];
    }
    return self;
}

#pragma mark - Public Methods

- (void)requestPermissionWithCompletion:(void(^)(BOOL granted))completion {
    [SFSpeechRecognizer requestAuthorization:^(SFSpeechRecognizerAuthorizationStatus status) {
        BOOL granted = status == SFSpeechRecognizerAuthorizationStatusAuthorized;
        
        [[AVAudioSession sharedInstance] requestRecordPermission:^(BOOL audioGranted) {
            dispatch_async(dispatch_get_main_queue(), ^{
                if (completion) {
                    completion(granted && audioGranted);
                }
            });
        }];
    }];
}

- (void)startRecordingWithCompletion:(void(^)(NSString *recognizedText, NSString *audioPath, NSError *error))completion {
    if (self.state != VoiceRecordingStateIdle) return;
    
    self.recordingCompletion = completion;
    self.isRealTimeMode = NO;
    
    // 设置录音会话
    NSError *error = nil;
    AVAudioSession *audioSession = [AVAudioSession sharedInstance];
    [audioSession setCategory:AVAudioSessionCategoryPlayAndRecord error:&error];
    if (error) {
        if (completion) completion(nil, nil, error);
        return;
    }
    
    // 设置录音文件路径
    NSString *fileName = [NSString stringWithFormat:@"recording_%@.m4a", [[NSUUID UUID] UUIDString]];
    NSString *documentsPath = NSSearchPathForDirectoriesInDomains(NSDocumentDirectory, NSUserDomainMask, YES).firstObject;
    NSString *filePath = [documentsPath stringByAppendingPathComponent:fileName];
    
    // 配置录音设置
    NSDictionary *settings = @{
        AVFormatIDKey: @(kAudioFormatMPEG4AAC),
        AVSampleRateKey: @44100.0,
        AVNumberOfChannelsKey: @1,
        AVEncoderAudioQualityKey: @(AVAudioQualityHigh)
    };
    
    // 创建录音器
    self.audioRecorder = [[AVAudioRecorder alloc] initWithURL:[NSURL fileURLWithPath:filePath]
                                                    settings:settings
                                                       error:&error];
    if (error) {
        if (completion) completion(nil, nil, error);
        return;
    }
    
    self.audioRecorder.delegate = self;
    [self.audioRecorder prepareToRecord];
    [self.audioRecorder record];
    self.state = VoiceRecordingStateRecording;
}

- (void)stopRecording {
    if (self.state != VoiceRecordingStateRecording) return;
    
    [self.audioRecorder stop];
    self.state = VoiceRecordingStateRecognizing;
    
    // 开始语音识别
    NSURL *audioURL = self.audioRecorder.url;
    SFSpeechURLRecognitionRequest *request = [[SFSpeechURLRecognitionRequest alloc] initWithURL:audioURL];
    request.shouldReportPartialResults = NO;
    
    [self.speechRecognizer recognitionTaskWithRequest:request
                                          resultHandler:^(SFSpeechRecognitionResult * _Nullable result,
                                                        NSError * _Nullable error) {
        NSString *recognizedText = result.bestTranscription.formattedString;
        if (self.recordingCompletion) {
            self.recordingCompletion(recognizedText, audioURL.path, error);
        }
        self.state = VoiceRecordingStateIdle;
    }];
}

- (void)startRealtimeRecordingWithBlock:(void(^)(NSString *partialText))onPartialResults
                             completion:(void(^)(NSString *finalText, NSError *error))completion {
    if (self.state != VoiceRecordingStateIdle) return;
    
    self.realtimePartialBlock = onPartialResults;
    self.realtimeCompletion = completion;
    self.isRealTimeMode = YES;
    
    NSError *error;
    AVAudioSession *audioSession = [AVAudioSession sharedInstance];
    [audioSession setCategory:AVAudioSessionCategoryRecord error:&error];
    if (error) {
        if (completion) completion(nil, error);
        return;
    }
    
    self.recognitionRequest = [[SFSpeechAudioBufferRecognitionRequest alloc] init];
    self.recognitionRequest.shouldReportPartialResults = YES;
    
    AVAudioInputNode *inputNode = self.audioEngine.inputNode;
    self.recognitionTask = [self.speechRecognizer recognitionTaskWithRequest:self.recognitionRequest
                                                                resultHandler:^(SFSpeechRecognitionResult * _Nullable result,
                                                                              NSError * _Nullable error) {
        if (result) {
            NSString *text = result.bestTranscription.formattedString;
            if (result.isFinal) {
                if (self.realtimeCompletion) {
                    self.realtimeCompletion(text, nil);
                }
            } else {
                if (self.realtimePartialBlock) {
                    self.realtimePartialBlock(text);
                }
            }
        }
        
        if (error) {
            [self.audioEngine stop];
            [inputNode removeTapOnBus:0];
            self.recognitionRequest = nil;
            self.recognitionTask = nil;
            self.state = VoiceRecordingStateIdle;
            
            if (self.realtimeCompletion) {
                self.realtimeCompletion(nil, error);
            }
        }
    }];
    
    AVAudioFormat *recordingFormat = [inputNode outputFormatForBus:0];
    [inputNode installTapOnBus:0 bufferSize:1024 format:recordingFormat
                        block:^(AVAudioPCMBuffer * _Nonnull buffer, AVAudioTime * _Nonnull when) {
        [self.recognitionRequest appendAudioPCMBuffer:buffer];
    }];
    
    [self.audioEngine prepare];
    [self.audioEngine startAndReturnError:&error];
    if (error) {
        if (completion) completion(nil, error);
        return;
    }
    
    self.state = VoiceRecordingStateRecording;
}

- (void)stopRealtimeRecording {
    if (self.state != VoiceRecordingStateRecording || !self.isRealTimeMode) return;
    
    [self.audioEngine stop];
    [self.recognitionRequest endAudio];
    [self.audioEngine.inputNode removeTapOnBus:0];
    
    self.recognitionRequest = nil;
    self.recognitionTask = nil;
    self.state = VoiceRecordingStateIdle;
}

- (void)playAudioWithUrl:(NSString *)urlString completion:(void(^)(NSError *error))completion {
    if (self.audioPlayer) {
        [self.audioPlayer stop];
        self.audioPlayer = nil;
    }
    
    NSError *error;
    self.audioPlayer = [[AVAudioPlayer alloc] initWithContentsOfURL:[NSURL fileURLWithPath:urlString]
                                                             error:&error];
    if (error) {
        if (completion) completion(error);
        return;
    }
    
    [self.audioPlayer play];
    if (completion) completion(nil);
}

- (void)stopPlaying {
    if (self.audioPlayer) {
        [self.audioPlayer stop];
        self.audioPlayer = nil;
    }
}

#pragma mark - AVAudioRecorderDelegate

- (void)audioRecorderDidFinishRecording:(AVAudioRecorder *)recorder successfully:(BOOL)flag {
    if (!flag && self.recordingCompletion) {
        NSError *error = [NSError errorWithDomain:@"com.kongfuzi.voice"
                                           code:-1
                                       userInfo:@{NSLocalizedDescriptionKey: @"Recording failed"}];
        self.recordingCompletion(nil, nil, error);
        self.state = VoiceRecordingStateIdle;
    }
}

#pragma mark - SFSpeechRecognizerDelegate

- (void)speechRecognizer:(SFSpeechRecognizer *)speechRecognizer availabilityDidChange:(BOOL)available {
    if (!available && self.state != VoiceRecordingStateIdle) {
        [self stopRecording];
        [self stopRealtimeRecording];
    }
}

@end 