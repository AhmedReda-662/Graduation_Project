import 'dart:async';
import 'dart:math';

import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:grad_project/core/theme/app_colors.dart';

class NumberSupermarketScreen extends StatefulWidget {
  const NumberSupermarketScreen({super.key});

  @override
  State<NumberSupermarketScreen> createState() =>
      _NumberSupermarketScreenState();
}

class _NumberSupermarketScreenState extends State<NumberSupermarketScreen>
    with TickerProviderStateMixin {
  int _targetSum = 10;
  int _currentSum = 0;
  int _score = 0;
  int _level = 1;

  final List<Map<String, dynamic>> _fruitsOnBelt = [];
  final Random _random = Random();
  late Ticker _ticker;
  Duration _lastElapsed = Duration.zero;

  late FlutterTts _flutterTts;

  late AnimationController _customerController;
  bool _isDancing = false;
  bool _isExploding = false;

  @override
  void initState() {
    super.initState();
    _initTts();
    _customerController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 500),
    );
    _ticker = createTicker(_onTick);
    _startGame();
  }

  void _initTts() async {
    _flutterTts = FlutterTts();
    await _flutterTts.setLanguage("en-US");
    await _flutterTts.setPitch(1.2);
    await _flutterTts.setSpeechRate(0.5); 
  }

  @override
  void dispose() {
    _ticker.dispose();
    _customerController.dispose();
    _flutterTts.stop();
    super.dispose();
  }

  void _startGame() {
    _score = 0;
    _level = 1;
    _startLevel();
    if (!_ticker.isActive) {
      _ticker.start();
    }
  }

  void _startLevel() {
    setState(() {
      _currentSum = 0;
      _targetSum = _random.nextInt(5 * _level) + 5; 
      _fruitsOnBelt.clear();
      _isDancing = false;
      _isExploding = false;
    });
    _speak("I need $_targetSum");
  }

  void _speak(String text) async {
    await _flutterTts.speak(text);
  }

  void _onTick(Duration elapsed) {
    if (!mounted) return;

    final double dt = (elapsed - _lastElapsed).inMilliseconds / 1000.0;
    _lastElapsed = elapsed;

    if (dt > 0.1) return;

    _updateFruits(dt);
    _checkSpawn();
  }

  void _checkSpawn() {
    if (_isDancing || _isExploding) return;

    final screenWidth = MediaQuery.of(context).size.width;
    final double minSpacing = 150.w; 
    final double variance = _random.nextDouble() * 100.w;

    bool canSpawn = false;

    if (_fruitsOnBelt.isEmpty) {
      canSpawn = true;
    } else {
     
      final lastFruitX = (_fruitsOnBelt.last['x'] as double);
      if (screenWidth - lastFruitX > minSpacing + variance) {
        canSpawn = true;
      }
    }

    if (canSpawn) {
      _spawnFruit(screenWidth);
    }
  }

  void _spawnFruit(double startX) {
 

    int value;
    int remaining = _targetSum - _currentSum;

    if (remaining > 0 && _random.nextDouble() < 0.4) {
      value = _random.nextInt(remaining) + 1;
    } else {
      value = _random.nextInt(_targetSum + 5) + 1;
    }

    final fruitTypes = [
      {'icon': "🍎", 'color': Colors.redAccent},
      {'icon': "🍌", 'color': Colors.yellow},
      {'icon': "🍇", 'color': Colors.purpleAccent},
      {'icon': "🍊", 'color': Colors.orangeAccent},
      {'icon': "🍉", 'color': Colors.greenAccent},
      {'icon': "🫐", 'color': Colors.blueAccent},
      {'icon': "🍓", 'color': Colors.pinkAccent},
    ];
    final type = fruitTypes[_random.nextInt(fruitTypes.length)];

    setState(() {
      _fruitsOnBelt.add({
        'id': DateTime.now().microsecondsSinceEpoch, 
        'value': value,
        'icon': type['icon'],
        'color': type['color'],
        'x': startX,
        'y': 50.h, 
        'scale': 0.0, 
      });
    });
  }

  void _updateFruits(double dt) {
    final double speed = 180.w + (_level * 15.w);

    setState(() {
      for (var fruit in _fruitsOnBelt) {
        fruit['x'] -= speed * dt;

        if (fruit['scale'] < 1.0) {
          fruit['scale'] += dt * 5; 
          if (fruit['scale'] > 1.0) fruit['scale'] = 1.0;
        }
      }
      _fruitsOnBelt.removeWhere((fruit) => fruit['x'] < -100.w);
    });
  }

  void _onFruitTap(Map<String, dynamic> fruit) {
    if (_isExploding || _isDancing) return;

    HapticFeedback.selectionClick();

    setState(() {
      _currentSum += (fruit['value'] as int);

      
      _fruitsOnBelt.removeWhere((f) => f['id'] == fruit['id']);
    });

    _checkSum();
  }

  void _checkSum() {
    if (_currentSum == _targetSum) {
      _handleSuccess();
    } else if (_currentSum > _targetSum) {
      _handleFailure();
    } else {
    }
  }

  void _handleSuccess() {
    setState(() {
      _isDancing = true;
      _score += 10;
      _level++;
    });

    _speak("Great Job!");
    _customerController.repeat(reverse: true);
    HapticFeedback.heavyImpact();

    Future.delayed(const Duration(seconds: 3), () {
      if (!mounted) return;
      _customerController.stop();
      _customerController.reset();
      _startLevel();
    });
  }

  void _handleFailure() {
    setState(() {
      _isExploding = true;
    });

    _speak("Oops! Too much!");
    HapticFeedback.vibrate();

    Future.delayed(const Duration(seconds: 2), () {
      if (!mounted) return;
      setState(() {
        _currentSum = 0;
        _isExploding = false;
      });
      _speak("Try again. I need $_targetSum");
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.lightBlue.shade50,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: AppColors.primary),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          "Number Supermarket",
          style: Theme.of(context).textTheme.displaySmall?.copyWith(
            fontSize: 22.sp,
            fontWeight: FontWeight.bold,
            color: AppColors.primary,
          ),
        ),
        actions: [
          Container(
            padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 6.h),
            margin: EdgeInsets.only(right: 15.w),
            decoration: BoxDecoration(
              color: AppColors.primary,
              borderRadius: BorderRadius.circular(20.r),
              boxShadow: const [
                BoxShadow(
                  color: Colors.black26,
                  blurRadius: 4,
                  offset: Offset(0, 2),
                ),
              ],
            ),
            child: Row(
              children: [
                Icon(Icons.star, color: Colors.yellowAccent, size: 20.sp),
                SizedBox(width: 5.w),
                Text(
                  "$_score",
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 18.sp,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            flex: 3,
            child: Stack(
              alignment: Alignment.center,
              children: [
                Positioned(
                  top: 20.h,
                  child: Icon(
                    Icons.storefront_rounded,
                    size: 200.sp,
                    color: Colors.blueGrey.withOpacity(0.2),
                  ),
                ),

                Positioned(
                  bottom: 0,
                  child: Container(
                    width: MediaQuery.of(context).size.width,
                    height: 25.h,
                    decoration: BoxDecoration(
                      color: Colors.grey.shade300,
                      border: Border(
                        top: BorderSide(color: Colors.grey.shade400, width: 2),
                      ),
                    ),
                  ),
                ),

                Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    _buildCustomer(),
                    SizedBox(height: 10.h),
                    _buildSpeechBubble(),
                  ],
                ),
              ],
            ),
          ),

          Expanded(
            flex: 3,
            child: Container(
              width: double.infinity,
              color: const Color(0xFFE0E0E0), 
              child: RepaintBoundary(
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    Positioned(
                      top: 40.h,
                      left: 0,
                      right: 0,
                      height: 120.h,
                      child: Container(
                        decoration: BoxDecoration(
                          color: const Color(0xFF333333),
                          border: Border.symmetric(
                            horizontal: BorderSide(
                              color: Colors.grey.shade800,
                              width: 5,
                            ),
                          ),
                        ),
                        child: ClipRect(
                          child: CustomPaint(
                            painter: BeltTexturePainter(
                              offset:
                                  (DateTime.now().millisecondsSinceEpoch / 10) %
                                  40,
                            ),
                            size: Size.infinite,
                          ),
                        ),
                      ),
                    ),

                    ..._fruitsOnBelt.map((fruit) {
                      return Positioned(
                        left: (fruit['x'] as double),
                        top: 55.h, // Centered on belt
                        child: Transform.scale(
                          scale: fruit['scale'],
                          child: GestureDetector(
                            onTap: () => _onFruitTap(fruit),
                            child: _buildFruitItem(fruit),
                          ),
                        ),
                      );
                    }),

                    Positioned(
                      bottom: 0,
                      left: 20.w,
                      child: _buildCashRegister(),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCustomer() {
    return AnimatedBuilder(
      animation: _customerController,
      builder: (context, child) {
        double bounce = 0;
        if (_isDancing) {
          bounce = sin(_customerController.value * 4 * pi) * 15;
        }
        double shakeX = 0;
        if (_isExploding) {
          shakeX = sin(DateTime.now().millisecondsSinceEpoch * 0.2) * 8;
        }

        return Transform.translate(
          offset: Offset(shakeX, -bounce),
          child: SizedBox(
            height: 200.h,
            width: 150.w,
            child: Stack(
              alignment: Alignment.bottomCenter,
              children: [
                _buildCashierBody(),
                _buildCashierHead(),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildCashierBody() {
    return Container(
      width: 100.w,
      height: 90.h,
      decoration: BoxDecoration(
        color: Colors.green.shade700, // Apron color
        borderRadius: BorderRadius.vertical(
          top: Radius.circular(40.r),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black26,
            blurRadius: 10,
            offset: Offset(0, 5),
          ),
        ],
      ),
      child: Center(
        child: Icon(
          Icons.store,
          color: Colors.white.withOpacity(0.5),
          size: 40.sp,
        ),
      ),
    );
  }

  Widget _buildCashierHead() {
    return Positioned(
      top: 10.h,
      child: Container(
        width: 90.w,
        height: 100.h,
        decoration: BoxDecoration(
          color: Color(0xFFFFD180),
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(
              color: Colors.black12,
              blurRadius: 5,
              offset: Offset(0, 2),
            ),
          ],
        ),
        child: Stack(
          children: [
            _buildCashierEyes(),
            _buildCashierMouth(),
            _buildCashierCap(),
          ],
        ),
      ),
    );
  }

  Widget _buildCashierEyes() {
    return SizedBox(
      width: 90.w,
      height: 100.h,
      child: Stack(
        children: [
          Positioned(
            top: 40.h,
            left: 20.w,
            child: CircleAvatar(
              backgroundColor: Colors.black,
              radius: 5.r,
            ),
          ),
          Positioned(
            top: 40.h,
            right: 20.w,
            child: CircleAvatar(
              backgroundColor: Colors.black,
              radius: 5.r,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCashierMouth() {
    return Positioned(
      bottom: 25.h,
      left: 30.w,
      child: Container(
        width: 30.w,
        height: 10.h,
        decoration: BoxDecoration(
          color: _isExploding ? Colors.transparent : Colors.redAccent,
          borderRadius: BorderRadius.circular(20),
          border:
              _isExploding ? Border.all(color: Colors.black, width: 2) : null,
        ),
      ),
    );
  }

  Widget _buildCashierCap() {
    return Positioned(
      top: 0,
      child: Container(
        width: 90.w,
        height: 30.h,
        decoration: BoxDecoration(
          color: Colors.green.shade800,
          borderRadius: BorderRadius.vertical(
            top: Radius.circular(40.r),
          ),
        ),
      ),
    );
  }

  Widget _buildSpeechBubble() {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 8.h),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20.r),
        border: Border.all(color: Colors.grey.shade300, width: 2),
        boxShadow: const [
          BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, 2)),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            "I need:",
            style: TextStyle(
              color: Colors.black87,
              fontSize: 16.sp,
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(width: 8.w),
          Text(
            "$_targetSum",
            style: TextStyle(
              fontSize: 24.sp,
              fontWeight: FontWeight.w900,
              color: AppColors.primary,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFruitItem(Map<String, dynamic> fruit) {
    return Container(
      width: 80.w,
      height: 80.w,
      decoration: BoxDecoration(
        color: Colors.white,
        shape: BoxShape.circle,
        // Removed BoxShadow for performance on moving items
        border: Border.all(color: fruit['color'].withOpacity(0.5), width: 2),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(fruit['icon'], style: TextStyle(fontSize: 32.sp)),
          Text(
            "${fruit['value']}",
            style: TextStyle(
              fontWeight: FontWeight.w900,
              fontSize: 18.sp,
              color: Colors.black87,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCashRegister() {
    return Container(
      padding: EdgeInsets.all(15.w),
      width: 160.w,
      decoration: BoxDecoration(
        color: Colors.blueGrey.shade100,
        borderRadius: BorderRadius.only(topRight: Radius.circular(20.r)),
        boxShadow: [BoxShadow(color: Colors.black26, blurRadius: 10)],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 5.h),
            decoration: BoxDecoration(
              color: Colors.black87,
              borderRadius: BorderRadius.circular(5.r),
              border: Border.all(color: Colors.grey.shade600, width: 2),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  "TOTAL",
                  style: TextStyle(
                    color: Colors.greenAccent,
                    fontSize: 12.sp,
                    fontFamily: 'Courier',
                  ),
                ),
                Text(
                  "$_currentSum",
                  style: TextStyle(
                    fontSize: 24.sp,
                    fontWeight: FontWeight.bold,
                    fontFamily: 'Courier',
                    color: _currentSum > _targetSum
                        ? Colors.redAccent
                        : (_currentSum == _targetSum
                              ? Colors.greenAccent
                              : Colors.white),
                  ),
                ),
              ],
            ),
          ),
          SizedBox(height: 5.h),
          // Register Keys Graphic
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: List.generate(
              4,
              (index) => Container(
                width: 25.w,
                height: 20.h,
                decoration: BoxDecoration(
                  color: Colors.grey.shade400,
                  borderRadius: BorderRadius.circular(3),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class BeltTexturePainter extends CustomPainter {
  final double offset;
  BeltTexturePainter({this.offset = 0});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.grey.shade800
      ..strokeWidth = 2;

    // Draw diagonal lines for belt texture
    // Use offset to create scrolling effect
    double startX = -50 + (offset % 20);
    for (double i = startX; i < size.width + 50; i += 20) {
      canvas.drawLine(Offset(i, 0), Offset(i - 20, size.height), paint);
    }
  }

  @override
  bool shouldRepaint(BeltTexturePainter oldDelegate) =>
      oldDelegate.offset != offset;
}
