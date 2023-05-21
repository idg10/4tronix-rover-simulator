import msvcrt

while True:
    key = msvcrt.getch()
    print("getch returned ", len(key), " bytes")
    for v in key:
        print(v)
