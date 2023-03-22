int fact(int x) {
	int y = x - 1;
	while (y > 0) {
		x = x * y;
		y = y - 1;
	}

	return x;
}

int main() {
	printf("%d\n", fact(5));
}
