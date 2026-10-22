#pragma once
#include <cmath>

namespace gameai {

// Mirror of Python core.vector.Vector2 (x, y as double).
struct Vector2 {
    double x = 0.0;
    double y = 0.0;

    Vector2() = default;
    Vector2(double x_, double y_) : x(x_), y(y_) {}

    Vector2 operator+(const Vector2& o) const { return {x + o.x, y + o.y}; }
    Vector2 operator-(const Vector2& o) const { return {x - o.x, y - o.y}; }
    Vector2 operator*(double s) const { return {x * s, y * s}; }
    Vector2 operator/(double s) const { return {x / s, y / s}; }

    double dot(const Vector2& o) const { return x * o.x + y * o.y; }
    double length_sq() const { return x * x + y * y; }
    double length() const { return std::hypot(x, y); }
    Vector2 normalized() const {
        double l = length();
        return l == 0.0 ? Vector2{} : (*this) / l;
    }
    double distance(const Vector2& o) const { return (*this - o).length(); }
};

}  // namespace gameai
