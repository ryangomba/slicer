// Copyright 2014-present Ryan Gomba. All Rights Reserved.

#import "ViewController.h"

@interface ViewController ()

@end

@implementation ViewController

- (void)viewDidLoad {
    [super viewDidLoad];
    
    NSArray *sliceNames = @[@"umbrella", @"headphones", @"cross"];
    [sliceNames enumerateObjectsUsingBlock:^(NSString *sliceName, NSUInteger i, BOOL *stop) {
        UIImageView *sliceView = [[UIImageView alloc] initWithImage:[UIImage imageNamed:sliceName]];
        CGFloat sliceViewCenterY = roundf(self.view.bounds.size.height / (sliceNames.count + 1) * (i + 1));
        sliceView.center = CGPointMake(self.view.bounds.size.width / 2, sliceViewCenterY);
        [self.view addSubview:sliceView];
    }];
}

@end
