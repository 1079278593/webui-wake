//
//  NSBundle+MJRefresh.m
//  MJRefreshExample
//
//  Created by MJ Lee on 16/6/13.
//  Copyright © 2016年 小码哥. All rights reserved.
//

#import "NSBundle+MJRefresh.h"
#import "MJRefreshComponent.h"
#import "MJRefreshConfig.h"

static NSBundle *mj_defaultI18nBundle = nil;
static NSBundle *mj_systemI18nBundle = nil;

@implementation NSBundle (MJRefresh)
+ (instancetype)mj_refreshBundle
{
    static NSBundle *refreshBundle = nil;
    if (refreshBundle == nil) {
#ifdef MJ_SPM
        NSBundle *containnerBundle = SWIFTPM_MODULE_BUNDLE;
#else
        NSBundle *containnerBundle = [NSBundle bundleForClass:[MJRefreshComponent class]];
#endif
        refreshBundle = [NSBundle bundleWithPath:[containnerBundle pathForResource:@"MJRefresh" ofType:@"bundle"]];
    }
    return refreshBundle;
}

+ (UIImage *)mj_arrowImage
{
    static UIImage *arrowImage = nil;
    if (arrowImage == nil) {
        arrowImage = [[UIImage imageWithContentsOfFile:[[self mj_refreshBundle] pathForResource:@"arrow@2x" ofType:@"png"]] imageWithRenderingMode:UIImageRenderingModeAlwaysTemplate];
    }
    return arrowImage;
}

+ (UIImage *)mj_trailArrowImage {
    static UIImage *arrowImage = nil;
    if (arrowImage == nil) {
        arrowImage = [[UIImage imageWithContentsOfFile:[[self mj_refreshBundle] pathForResource:@"trail_arrow@2x" ofType:@"png"]] imageWithRenderingMode:UIImageRenderingModeAlwaysTemplate];
    }
    return arrowImage;
}

+ (NSString *)mj_localizedStringForKey:(NSString *)key
{
    return [self mj_localizedStringForKey:key value:nil];
}

+ (NSString *)mj_localizedStringForKey:(NSString *)key value:(NSString *)value
{
    NSBundle *bundle = nil;
//    if (bundle == nil) {
        NSString *language = MJRefreshConfig.defaultConfig.languageCode;
        // 如果配置中没有配置语言zh-Hans
        if (language.length == 0) {
            // （iOS获取的语言字符串比较不稳定）目前框架只处理en、zh-Hans、zh-Hant三种情况，其他按照系统默认处理
            language = [NSLocale preferredLanguages].firstObject;
        }
        
        if ([language hasPrefix:@"en"]) {
            language = @"en";
        } else if ([language hasPrefix:@"zh"]) {
            if ([language rangeOfString:@"Hans"].location != NSNotFound) {
                language = @"zh-Hans"; // 简体中文
            } else { // zh-Hant\zh-HK\zh-TW
                language = @"zh-Hant"; // 繁體中文
            }
        } else if ([language hasPrefix:@"ko"]) {
            language = @"ko";
        } else {
            language = @"en";
        }
        
        // 从MJRefresh.bundle中查找资源
        bundle = [NSBundle bundleWithPath:[[NSBundle mj_refreshBundle] pathForResource:language ofType:@"lproj"]];
//    }
    value = [bundle localizedStringForKey:key value:value table:nil];
    return [[NSBundle mainBundle] localizedStringForKey:key value:value table:nil];
}

+ (NSBundle *)mj_defaultI18nBundleWithLanguage:(NSString *)language {
    if ([language hasPrefix:@"en"]) {
        language = @"en";
    } else if ([language hasPrefix:@"zh"]) {
        if ([language rangeOfString:@"Hans"].location != NSNotFound) {
            language = @"zh-Hans"; // 简体中文
        } else { // zh-Hant\zh-HK\zh-TW
            language = @"zh-Hant"; // 繁體中文
        }
    } else if ([language hasPrefix:@"ko"]) {
        language = @"ko";
    } else if ([language hasPrefix:@"ru"]) {
        language = @"ru";
    } else if ([language hasPrefix:@"uk"]) {
        language = @"uk";
    } else {
        language = @"en";
    }
    
    // 从MJRefresh.bundle中查找资源
    return [NSBundle bundleWithPath:[[NSBundle mj_refreshBundle] pathForResource:language ofType:@"lproj"]];
}
@end

@implementation MJRefreshConfig (Bundle)

+ (void)resetLanguageResourceCache {
    mj_defaultI18nBundle = nil;
    mj_systemI18nBundle = nil;
}

@end
