#import <Foundation/Foundation.h>
#import <Speech/Speech.h>
#import <AVFoundation/AVFoundation.h>

typedef NS_ENUM(NSInteger, VoiceRecordingState) {
    VoiceRecordingStateIdle,
    VoiceRecordingStateRecording,
    VoiceRecordingStateRecognizing
};

@interface VoiceManager : NSObject

@property (nonatomic, assign, readonly) VoiceRecordingState state;
@property (nonatomic, assign, readonly) BOOL isRealTimeMode;

+ (instancetype)sharedManager;

// 语音识别权限
- (void)requestPermissionWithCompletion:(void(^)(BOOL granted))completion;

// 普通语音输入
- (void)startRecordingWithCompletion:(void(^)(NSString *recognizedText, NSString *audioPath, NSError *error))completion;
- (void)stopRecording;

// 实时语音识别
- (void)startRealtimeRecordingWithBlock:(void(^)(NSString *partialText))onPartialResults
                             completion:(void(^)(NSString *finalText, NSError *error))completion;
- (void)stopRealtimeRecording;

// 语音播放
- (void)playAudioWithUrl:(NSString *)urlString completion:(void(^)(NSError *error))completion;
- (void)stopPlaying;

@end 