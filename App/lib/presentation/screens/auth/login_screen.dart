import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:animate_do/animate_do.dart';
import 'package:grad_project/core/theme/app_colors.dart';
import '../home/home_screen.dart';
import '../progress/progress_screen.dart';
import 'signup_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  bool isParent = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: EdgeInsets.symmetric(horizontal: 24.w, vertical: 20.h),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              SizedBox(height: 20.h),
              FadeInDown(
                child: Text(
                  "Welcome Back!",
                  style: Theme.of(context).textTheme.displayLarge,
                  textAlign: TextAlign.center,
                ),
              ),
              SizedBox(height: 10.h),
              FadeInDown(
                delay: const Duration(milliseconds: 200),
                child: Text(
                  "Who is logging in today?",
                  style: Theme.of(context).textTheme.bodyLarge,
                  textAlign: TextAlign.center,
                ),
              ),

              SizedBox(height: 30.h),

              Container(
                padding: EdgeInsets.all(5.w),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(20.r),
                  border: Border.all(color: Colors.grey.shade300),
                ),
                child: Row(
                  children: [
                    Expanded(child: _buildRoleButton("Student", !isParent)),
                    Expanded(child: _buildRoleButton("Parent", isParent)),
                  ],
                ),
              ),

              SizedBox(height: 40.h),

              // Form
              FadeInUp(
                child: Column(
                  children: [
                    _buildTextField(
                      label: "Email / Username",
                      icon: Icons.person_rounded,
                    ),
                    SizedBox(height: 20.h),
                    _buildTextField(
                      label: "Password",
                      icon: Icons.lock_rounded,
                      isObscure: true,
                    ),
                  ],
                ),
              ),

              SizedBox(height: 40.h),

              // Login Button
              FadeInUp(
                delay: const Duration(milliseconds: 400),
                child: SizedBox(
                  height: 60.h,
                  child: ElevatedButton(
                    onPressed: () {
                      if (isParent) {
                        Navigator.pushReplacement(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const ProgressScreen(),
                          ),
                        );
                      } else {
                        Navigator.pushReplacement(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const HomeScreen(),
                          ),
                        );
                      }
                    },
                    child: const Text("Login"),
                  ),
                ),
              ),

              SizedBox(height: 20.h),

              // Signup Link
              FadeInUp(
                delay: const Duration(milliseconds: 600),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      "Don't have an account? ",
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                    GestureDetector(
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const SignupScreen(),
                          ),
                        );
                      },
                      child: Text(
                        "Sign Up",
                        style: TextStyle(
                          color: AppColors.primary,
                          fontWeight: FontWeight.bold,
                          fontSize: 16.sp,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildRoleButton(String title, bool isSelected) {
    return GestureDetector(
      onTap: () {
        setState(() {
          isParent = title == "Parent";
        });
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        padding: EdgeInsets.symmetric(vertical: 15.h),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.yellow : Colors.transparent,
          borderRadius: BorderRadius.circular(15.r),
        ),
        child: Center(
          child: Text(
            title,
            style: TextStyle(
              color: isSelected
                  ? AppColors.textPrimary
                  : AppColors.textSecondary,
              fontWeight: FontWeight.bold,
              fontSize: 18.sp,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTextField({
    required String label,
    required IconData icon,
    bool isObscure = false,
  }) {
    return TextField(
      obscureText: isObscure,
      style: TextStyle(fontSize: 18.sp),
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, color: AppColors.primaryAccent),
      ),
    );
  }
}
