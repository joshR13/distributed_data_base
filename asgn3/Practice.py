from VectorClocks import *

def main():

    viewList = ["10.10.0.2:8085", "10.10.0.3:8085", "10.10.0.4:8085"]

    vectorClock = VectorClocks(viewList)

    VC1 = {"10.10.0.2": 0, "10.10.0.3": 6, "10.10.0.4": 7}

    VC2 = {"10.10.0.2": 1, "10.10.0.3": 5, "10.10.0.4": 8}

    #IN this case, VC1 is greater than VC2

    print("This is result from VcComparator: " + vectorClock.VcComparator(VC1, VC2))


if __name__ == '__main__':
    main()