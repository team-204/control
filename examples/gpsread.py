"""Reads 10 gps outputs from the serial connection"""
import pprint
import control.gps


def main():
    """Reads 10 gps outputs from the serial connection"""
    gps = control.gps.Gps('/dev/ttyO4', 9600)
    for i in range(10):
        gps_data = gps.read()
        pprint.pprint(gps_data)


if __name__ == "__main__":
    main()
