#include <stdio.h>

int iterative_fact(int x) {
	int y;
	y = x - 1;

	while (y > 0) {
		x = x * y;
		y = y - 1;
	}

	return x;
}

int recursive_fact(int x) {
	if (x <= 0) {
		return 1;
	}

	return x * recursive_fact(x - 1);
}

int main() {
	print recursive_fact(5);
	print iterative_fact(5);
}
