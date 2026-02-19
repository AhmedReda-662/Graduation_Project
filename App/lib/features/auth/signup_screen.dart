import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:grad_project/core/theme/app_colors.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';
import 'package:fluttertoast/fluttertoast.dart';
import 'login_screen.dart';

class SignupScreen extends StatefulWidget {
  const SignupScreen({super.key});

  @override
  State<SignupScreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends State<SignupScreen> {
  bool isParent = false;
  File? _profileImage;
  final ImagePicker _picker = ImagePicker();

  Future<void> _pickImage() async {
    final XFile? pickedFile = await _picker.pickImage(
      source: ImageSource.gallery,
    );
    if (pickedFile != null) {
      setState(() {
        _profileImage = File(pickedFile.path);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: EdgeInsets.symmetric(horizontal: 24.w),
          child: Column(
            children: [
              Text(
                "Create Account",
                style: Theme.of(context).textTheme.displayLarge,
              ),
              SizedBox(height: 10.h),
              Text(
                "Sign up to start learning!",
                style: Theme.of(context).textTheme.bodyLarge,
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

              SizedBox(height: 30.h),

              GestureDetector(
                onTap: _pickImage,
                child: CircleAvatar(
                  radius: 50.r,
                  backgroundColor: Colors.white,
                  backgroundImage: _profileImage != null
                      ? FileImage(_profileImage!)
                      : null,
                  child: _profileImage == null
                      ? Stack(
                          children: [
                            Align(
                              alignment: Alignment.center,
                              child: Icon(
                                Icons.camera_alt_rounded,
                                size: 40.sp,
                                color: Colors.grey.shade400,
                              ),
                            ),
                            Align(
                              alignment: Alignment.bottomRight,
                              child: CircleAvatar(
                                radius: 15.r,
                                backgroundColor: AppColors.primary,
                                child: Icon(
                                  Icons.add,
                                  color: Colors.white,
                                  size: 15.sp,
                                ),
                              ),
                            ),
                          ],
                        )
                      : null,
                ),
              ),
              SizedBox(height: 10.h),
              Text(
                "Upload Profile Photo",
                style: TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 14.sp,
                ),
              ),

              SizedBox(height: 30.h),

              SizedBox(height: 30.h),

              Row(
                children: [
                  Expanded(
                    child: _buildTextField(
                      label: "First Name",
                      icon: Icons.person,
                    ),
                  ),
                  SizedBox(width: 10.w),
                  Expanded(
                    child: _buildTextField(
                      label: "Last Name",
                      icon: Icons.person_outline,
                    ),
                  ),
                ],
              ),
              SizedBox(height: 20.h),

              if (!isParent) ...[
                _buildTextField(
                  label: "Age",
                  icon: Icons.cake,
                  inputType: TextInputType.number,
                ),
                SizedBox(height: 20.h),

                Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16.r),
                    border: Border.all(color: Colors.transparent),
                  ),
                  child: DropdownButtonFormField<String>(
                    decoration: InputDecoration(
                      labelText: "Select Disability",
                      prefixIcon: Icon(
                        Icons.accessibility_new,
                        color: AppColors.primaryAccent,
                      ),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(16.r),
                        borderSide: BorderSide.none,
                      ),
                      filled: true,
                      fillColor: Colors.white,
                    ),
                    items: const [
                      DropdownMenuItem(value: "None", child: Text("None")),
                      DropdownMenuItem(value: "ADHD", child: Text("ADHD")),
                      DropdownMenuItem(
                        value: "Tetraplegia",
                        child: Text("Tetraplegia"),
                      ),
                    ],
                    onChanged: (value) {},
                  ),
                ),
                SizedBox(height: 20.h),
              ],

              if (isParent) ...[
                _buildTextField(
                  label: "Student Email",
                  icon: Icons.school,
                  inputType: TextInputType.emailAddress,
                ),
                SizedBox(height: 20.h),
              ],

              _buildTextField(
                label: "Email",
                icon: Icons.email_rounded,
                inputType: TextInputType.emailAddress,
              ),
              SizedBox(height: 20.h),

              _buildTextField(
                label: "Password",
                icon: Icons.lock_rounded,
                isObscure: true,
              ),

              SizedBox(height: 40.h),
              SizedBox(
                width: double.infinity,
                height: 60.h,
                child: ElevatedButton(
                  onPressed: () {
                    Fluttertoast.showToast(
                      msg: "Registration Successful! Please Login.",
                      toastLength: Toast.LENGTH_SHORT,
                      gravity: ToastGravity.BOTTOM,
                      timeInSecForIosWeb: 1,
                      backgroundColor: Colors.green,
                      textColor: Colors.white,
                      fontSize: 16.0,
                    );

                    Navigator.pushReplacement(
                      context,
                      MaterialPageRoute(
                        builder: (context) => const LoginScreen(),
                      ),
                    );
                  },
                  child: const Text("Sign Up"),
                ),
              ),
              SizedBox(height: 20.h),

              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    "Already have an account? ",
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  GestureDetector(
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const LoginScreen(),
                        ),
                      );
                    },
                    child: Text(
                      "Login",
                      style: TextStyle(
                        color: AppColors.primary,
                        fontWeight: FontWeight.bold,
                        fontSize: 16.sp,
                      ),
                    ),
                  ),
                ],
              ),
              SizedBox(height: 40.h),
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
    TextInputType? inputType,
  }) {
    return TextField(
      obscureText: isObscure,
      keyboardType: inputType,
      style: TextStyle(fontSize: 18.sp),
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, color: AppColors.primaryAccent),
      ),
    );
  }
}
