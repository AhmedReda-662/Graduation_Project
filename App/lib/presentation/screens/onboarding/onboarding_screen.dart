import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:animate_do/animate_do.dart';
import 'package:grad_project/core/theme/app_colors.dart';

import '../auth/login_screen.dart';

class OnboardingScreen extends StatelessWidget {
  const OnboardingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFFDF6EC),
      body: SafeArea(
        child: Column(
          children: [
            SizedBox(height: 40.h),

            Expanded(
              flex: 3,
              child: FadeInDown(
                child: Container(
                  margin: EdgeInsets.all(20.w),
                  child: Image.asset(
                    'assets/images/onboarding.png',
                    fit: BoxFit.contain,
                  ),
                ),
              ),
            ),

            Expanded(
              flex: 2,
              child: Container(
                padding: EdgeInsets.symmetric(horizontal: 24.w),
                child: Column(
                  children: [
                    FadeInUp(
                      child: Text(
                        'Innovative learning\nmodern learner',
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.displayLarge
                            ?.copyWith(
                              color: AppColors.textPrimary,
                              height: 1.2,
                            ),
                      ),
                    ),
                    SizedBox(height: 16.h),
                    FadeInUp(
                      delay: const Duration(milliseconds: 200),
                      child: Text(
                        'It is a long established fact that a reader will by the readable content of a page when.',
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ),
                    SizedBox(height: 40.h),

                    SizedBox(height: 40.h),

                    FadeInUp(
                      delay: const Duration(milliseconds: 400),
                      child: SizedBox(
                        width: double.infinity,
                        height: 60.h,
                        child: ElevatedButton(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.primary,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(20.r),
                            ),
                            elevation: 5,
                            shadowColor: AppColors.primary.withValues(
                              alpha: 0.5,
                            ),
                          ),
                          onPressed: () {
                            Navigator.pushReplacement(
                              context,
                              MaterialPageRoute(
                                builder: (context) => const LoginScreen(),
                              ),
                            );
                          },
                          child: Text(
                            textAlign: TextAlign.center,
                            "Let's go!",
                            style: TextStyle(
                              fontSize: 20.sp,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
