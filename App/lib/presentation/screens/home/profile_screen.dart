import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:grad_project/core/theme/app_colors.dart';
import 'package:grad_project/presentation/screens/auth/login_screen.dart';
import 'dart:io';

class ProfileScreen extends StatelessWidget {
  final File? profileImage;
  const ProfileScreen({super.key, this.profileImage});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 20.h),
          child: Column(
            children: [
              Text(
                "My Profile",
                style: Theme.of(context).textTheme.displaySmall,
              ),
              SizedBox(height: 30.h),

              SizedBox(height: 30.h),

              CircleAvatar(
                radius: 60.r,
                backgroundColor: Colors.white,
                backgroundImage: profileImage != null
                    ? FileImage(profileImage!)
                    : null,
                child: profileImage == null
                    ? Icon(Icons.person, size: 60.sp, color: Colors.grey)
                    : null,
              ),
              SizedBox(height: 15.h),

              SizedBox(height: 15.h),

              Text(
                "Ahmed",
                style: TextStyle(
                  fontSize: 24.sp,
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
              ),
              Text(
                "Student",
                style: TextStyle(
                  fontSize: 16.sp,
                  color: AppColors.textSecondary,
                ),
              ),

              SizedBox(height: 40.h),

              SizedBox(height: 40.h),

              _buildOptionTile(
                icon: Icons.settings,
                title: "Settings",
                onTap: () {},
              ),
              _buildOptionTile(
                icon: Icons.notifications,
                title: "Notifications",
                onTap: () {},
              ),
              _buildOptionTile(
                icon: Icons.help,
                title: "Help & Support",
                onTap: () {},
              ),

              SizedBox(height: 40.h),

              SizedBox(height: 40.h),

              SizedBox(
                width: double.infinity,
                height: 60.h,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.redAccent,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(15.r),
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
                  child: const Text(
                    "Logout",
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildOptionTile({
    required IconData icon,
    required String title,
    required VoidCallback onTap,
  }) {
    return Container(
      margin: EdgeInsets.only(bottom: 15.h),
      child: ListTile(
        onTap: onTap,
        tileColor: Colors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(15.r),
        ),
        leading: Container(
          padding: EdgeInsets.all(8.w),
          decoration: BoxDecoration(
            color: AppColors.primary.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(10.r),
          ),
          child: Icon(icon, color: AppColors.primary),
        ),
        title: Text(
          title,
          style: TextStyle(
            fontSize: 16.sp,
            fontWeight: FontWeight.bold,
            color: AppColors.textPrimary,
          ),
        ),
        trailing: Icon(
          Icons.arrow_forward_ios,
          size: 16.sp,
          color: Colors.grey,
        ),
      ),
    );
  }
}
