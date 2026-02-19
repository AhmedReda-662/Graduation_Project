import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:grad_project/core/theme/app_colors.dart';
import 'package:grad_project/features/home/lessons_screen.dart';
import 'package:grad_project/features/progress/progress_screen.dart';
import 'package:grad_project/features/home/profile_screen.dart';

import 'dart:io';

class HomeScreen extends StatefulWidget {
  final File? profileImage;
  const HomeScreen({super.key, this.profileImage});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;

  late final List<Widget> _screens;

  @override
  void initState() {
    super.initState();
    _screens = [
      _HomeContent(profileImage: widget.profileImage),
      const ProgressScreen(),
      ProfileScreen(profileImage: widget.profileImage),
    ];
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: IndexedStack(index: _currentIndex, children: _screens),
      bottomNavigationBar: _buildBottomNav(),
    );
  }

  Widget _buildBottomNav() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.only(
          topLeft: Radius.circular(30.r),
          topRight: Radius.circular(30.r),
        ),
        boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 10)],
      ),
      child: BottomNavigationBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        type: BottomNavigationBarType.fixed,
        selectedItemColor: AppColors.primary,
        unselectedItemColor: Colors.grey,
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
          BottomNavigationBarItem(
            icon: Icon(Icons.bar_chart),
            label: 'Progress',
          ),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
    );
  }
}

class _HomeContent extends StatelessWidget {
  final File? profileImage;
  const _HomeContent({required this.profileImage});

  @override
  Widget build(BuildContext context) {
    return _buildStandardContent(context);
  }

  Widget _buildStandardContent(BuildContext context) {
    return SafeArea(
      child: SingleChildScrollView(
        padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 20.h),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(context),
            SizedBox(height: 30.h),

            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  "Learning path",
                  style: Theme.of(context).textTheme.displayMedium,
                ),
                TextButton(
                  onPressed: () {},
                  child: Text(
                    "View all",
                    style: TextStyle(color: AppColors.primary, fontSize: 16.sp),
                  ),
                ),
              ],
            ),

            SizedBox(height: 10.h),
            Text(
              "long established fact that a reader will be",
              style: Theme.of(context).textTheme.bodyMedium,
            ),

            SizedBox(height: 20.h),

            _buildCourseGrid(context),

            SizedBox(height: 100.h),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            RichText(
              text: TextSpan(
                style: TextStyle(
                  fontSize: 24.sp,
                  color: AppColors.textPrimary,
                  fontFamily: 'Fredoka',
                ),
                children: [
                  const TextSpan(text: "Hi "),
                  TextSpan(
                    text: "Ahmed",
                    style: TextStyle(
                      color: AppColors.primaryAccent,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
            SizedBox(height: 5.h),
            Text(
              "Let's learn something new today!",
              style: TextStyle(fontSize: 14.sp, color: AppColors.textSecondary),
            ),
          ],
        ),
        CircleAvatar(
          radius: 25.r,
          backgroundColor: Colors.grey.shade300,
          backgroundImage: profileImage != null
              ? FileImage(profileImage!)
              : null,
          child: profileImage == null
              ? Icon(Icons.person, color: Colors.white, size: 30.sp)
              : null,
        ),
      ],
    );
  }

  Widget _buildCourseGrid(BuildContext context) {
    final items = [
      {
        'color': const Color(0xFFFFECB3),
        'title': 'Letters-1',
        'progress': '6/6',
        'image': 'assets/images/lesson1.png',
      },
      {
        'color': const Color(0xFFC8E6C9),
        'title': 'Letters-2',
        'progress': '4/6',
        'image': 'assets/images/lesson2.png',
      },
      {
        'color': const Color(0xFFFFCCBC),
        'title': 'Letters-3',
        'progress': '2/6',
        'image': 'assets/images/lesson3.png',
      },
      {
        'color': const Color(0xFFBBDEFB),
        'title': 'Letters-4',
        'progress': '0/6',
        'image': 'assets/images/lesson4.png',
      },
    ];

    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      padding: EdgeInsets.only(bottom: 20.h),
      itemCount: items.length,
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 15.w,
        mainAxisSpacing: 15.h,
        childAspectRatio: 0.8,
      ),
      itemBuilder: (context, index) {
        final item = items[index];
        final isSelected = index == 3;

        return GestureDetector(
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => LessonsScreen(
                  courseTitle: item['title'] as String,
                  courseColor: item['color'] as Color,
                ),
              ),
            );
          },
          child: Container(
            decoration: BoxDecoration(
              color: item['color'] as Color,
              borderRadius: BorderRadius.circular(20.r),
              border: isSelected
                  ? Border.all(color: Colors.purple, width: 3)
                  : null,
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Expanded(
                  child: Padding(
                    padding: EdgeInsets.all(10.w),
                    child: Image.asset(
                      item['image'] as String,
                      fit: BoxFit.contain,
                    ),
                  ),
                ),
                Text(
                  item['title'] as String,
                  style: TextStyle(
                    fontSize: 18.sp,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                SizedBox(height: 5.h),
                Text(
                  item['progress'] as String,
                  style: TextStyle(
                    fontSize: 14.sp,
                    color: Colors.grey.shade700,
                  ),
                ),
                SizedBox(height: 10.h),
              ],
            ),
          ),
        );
      },
    );
  }
}
