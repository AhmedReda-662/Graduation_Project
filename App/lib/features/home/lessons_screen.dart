import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:grad_project/core/theme/app_colors.dart';
import 'package:animate_do/animate_do.dart';
import 'learning_game_screen.dart';
import 'number_supermarket_screen.dart';

class LessonsScreen extends StatelessWidget {
  final String courseTitle;
  final Color courseColor;

  const LessonsScreen({
    super.key,
    required this.courseTitle,
    required this.courseColor,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: courseColor,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios, color: AppColors.textPrimary),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          courseTitle,
          style: Theme.of(
            context,
          ).textTheme.displaySmall?.copyWith(fontSize: 24.sp),
        ),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 20.h),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              "Select a Lesson",
              style: Theme.of(context).textTheme.displayMedium,
            ),
            SizedBox(height: 20.h),

            ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: 5,
              itemBuilder: (context, index) {
                return FadeInUp(
                  delay: Duration(milliseconds: index * 100),
                  child: _buildLessonCard(context, index + 1),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLessonCard(BuildContext context, int lessonNum) {
    return GestureDetector(
      onTap: () {
        if (lessonNum == 1) {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => const NumberSupermarketScreen(),
            ),
          );
        } else {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => LearningGameScreen(
                lessonTitle: "$courseTitle - Lesson $lessonNum",
              ),
            ),
          );
        }
      },
      child: Container(
        margin: EdgeInsets.only(bottom: 15.h),
        padding: EdgeInsets.all(15.w),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20.r),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.05),
              blurRadius: 10,
              offset: const Offset(0, 5),
            ),
          ],
        ),
        child: Row(
          children: [
            Container(
              width: 60.w,
              height: 60.w,
              decoration: BoxDecoration(
                color: courseColor.withValues(alpha: 0.3),
                borderRadius: BorderRadius.circular(15.r),
              ),
              child: Center(
                child: Text(
                  "$lessonNum",
                  style: TextStyle(
                    fontSize: 24.sp,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                  ),
                ),
              ),
            ),
            SizedBox(width: 20.w),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    "Lesson $lessonNum",
                    style: TextStyle(
                      fontSize: 18.sp,
                      fontWeight: FontWeight.bold,
                      color: AppColors.textPrimary,
                    ),
                  ),
                  SizedBox(height: 5.h),
                  Text(
                    "Lesson",
                    style: TextStyle(
                      fontSize: 14.sp,
                      color: AppColors.textSecondary,
                    ),
                  ),
                ],
              ),
            ),
            Icon(Icons.play_circle_fill, color: AppColors.primary, size: 40.sp),
          ],
        ),
      ),
    );
  }
}
