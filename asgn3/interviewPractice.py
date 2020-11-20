def duplicateDetector():
    arrayOfStrings = ['bungus', 'dingus', 'dingus', 'parallelopiped']

    arrayOfStrings.sort() 

    print(arrayOfStrings)



    for x in range(len(arrayOfStrings)):

        if x == (len(arrayOfStrings) - 1):
            print("There are no duplicates.")
            break
        if arrayOfStrings[x + 1] == arrayOfStrings[x]:
            print("There is at least one dupilcated string.")
            break
        
