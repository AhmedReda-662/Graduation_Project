import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:grad_project/core/theme/app_colors.dart';
import 'package:animate_do/animate_do.dart';

class LearningGameScreen extends StatefulWidget {
  final String lessonTitle;

  const LearningGameScreen({super.key, required this.lessonTitle});

  @override
  State<LearningGameScreen> createState() => _LearningGameScreenState();
}

class _LearningGameScreenState extends State<LearningGameScreen> {
  int _currentQuestionIndex = 0;
  int _score = 0;
  bool _isCompleted = false;
  bool _answered = false;

  final List<Map<String, dynamic>> _questions = [
    {
      'question': 'Which is the letter A?',
      'options': ['B', 'A', 'C', 'D'],
      'answer': 'A',
      'color': AppColors.orange,
    },
    {
      'question': 'Find the Red color',
      'options': ['Blue', 'Green', 'Red', 'Yellow'],
      'answer': 'Red',
      'color': AppColors.primary,
    },
    {
      'question': 'Which number is 5?',
      'options': ['2', '5', '8', '1'],
      'answer': '5',
      'color': AppColors.purple,
    },
    {
      'question': 'Find the Cat',
      'options': ['Dog', 'Bird', 'Cat', 'Fish'],
      'answer': 'Cat',
      'color': AppColors.green,
    },
  ];

  void _handleAnswer(String selectedOption) {
    if (_answered) return;

    setState(() {
      _answered = true;
      if (selectedOption == _questions[_currentQuestionIndex]['answer']) {
        _score++;
      }
    });

    Future.delayed(const Duration(milliseconds: 1000), () {
      if (_currentQuestionIndex < _questions.length - 1) {
        setState(() {
          _currentQuestionIndex++;
          _answered = false;
        });
      } else {
        setState(() {
          _isCompleted = true;
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios, color: AppColors.primary),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          "Quiz Time!",
          style: Theme.of(
            context,
          ).textTheme.displaySmall?.copyWith(fontSize: 24.sp),
        ),
        centerTitle: true,
      ),
      body: _isCompleted ? _buildCompletionView() : _buildGameView(),
    );
  }

  Widget _buildGameView() {
    final question = _questions[_currentQuestionIndex];

    return Padding(
      padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 20.h),
      child: Column(
        children: [
          LinearProgressIndicator(
            value: (_currentQuestionIndex + 1) / _questions.length,
            backgroundColor: Colors.grey.shade300,
            valueColor: const AlwaysStoppedAnimation<Color>(AppColors.green),
            minHeight: 10.h,
            borderRadius: BorderRadius.circular(10.r),
          ),
          SizedBox(height: 10.h),
          Text(
            "Question ${_currentQuestionIndex + 1}/${_questions.length}",
            style: TextStyle(fontSize: 14.sp, color: AppColors.textSecondary),
          ),

          SizedBox(height: 40.h),

          FadeInDown(
            key: ValueKey(_currentQuestionIndex),
            child: Container(
              padding: EdgeInsets.all(30.w),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(25.r),
                boxShadow: [
                  BoxShadow(
                    color: question['color'].withValues(alpha: 0.2),
                    blurRadius: 15,
                    offset: const Offset(0, 5),
                  ),
                ],
              ),
              child: Column(
                children: [
                  Icon(
                    Icons.help_outline,
                    size: 50.sp,
                    color: question['color'],
                  ),
                  SizedBox(height: 20.h),
                  Text(
                    question['question'],
                    style: TextStyle(
                      fontSize: 24.sp,
                      fontWeight: FontWeight.bold,
                      color: AppColors.textPrimary,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          ),

          const Spacer(),

          Expanded(
            flex: 2,
            child: GridView.builder(
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                crossAxisSpacing: 20.w,
                mainAxisSpacing: 20.h,
                childAspectRatio: 1.2,
              ),
              itemCount: (question['options'] as List).length,
              itemBuilder: (context, index) {
                final option = question['options'][index];
                return FadeInUp(
                  delay: Duration(milliseconds: index * 100),
                  child: _buildOptionButton(option, question['answer']),
                );
              },
            ),
          ),
          SizedBox(height: 20.h),
        ],
      ),
    );
  }

  Widget _buildOptionButton(String option, String correctAnswer) {
    Color bgColor = Colors.white;
    Color borderColor = Colors.grey.shade200;
    Color textColor = AppColors.textPrimary;

    if (_answered) {
      if (option == correctAnswer) {
        bgColor = AppColors.green;
        borderColor = AppColors.green;
        textColor = Colors.white;
      } else if (option != correctAnswer) {
        bgColor = Colors.grey.shade100;
        textColor = Colors.grey;
      }
    }

    return GestureDetector(
      onTap: () => _handleAnswer(option),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        decoration: BoxDecoration(
          color: bgColor,
          borderRadius: BorderRadius.circular(20.r),
          border: Border.all(color: borderColor, width: 2),
          boxShadow: [
            if (!_answered)
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.05),
                blurRadius: 5,
                offset: const Offset(0, 3),
              ),
          ],
        ),
        child: Center(
          child: Text(
            option,
            style: TextStyle(
              fontSize: 22.sp,
              fontWeight: FontWeight.bold,
              color: textColor,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildCompletionView() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          FadeInDown(
            child: Icon(
              Icons.emoji_events,
              size: 100.sp,
              color: AppColors.yellow,
            ),
          ),
          SizedBox(height: 20.h),
          FadeInUp(
            child: Text(
              "Awesome Job!",
              style: Theme.of(context).textTheme.displayLarge,
            ),
          ),
          SizedBox(height: 10.h),
          Text(
            "You scored $_score/${_questions.length}",
            style: TextStyle(fontSize: 20.sp, color: AppColors.textSecondary),
          ),
          SizedBox(height: 50.h),
          FadeInUp(
            delay: const Duration(milliseconds: 200),
            child: SizedBox(
              width: 200.w,
              height: 50.h,
              child: ElevatedButton(
                onPressed: () {
                  Navigator.pop(context);
                },
                child: const Text("Finish"),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
