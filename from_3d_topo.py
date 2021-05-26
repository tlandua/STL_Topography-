import trimesh
import numpy as np
import csv
import sys


def from_3d_generate(filename, output, convert, debug, write_to_file, Nx, Ny):
    my_mesh = trimesh.load(filename)
    debug = debug
    write_to_file = write_to_file

    if convert == 'Inches':
        for i in range(len(my_mesh.vertices + 1)):
            for j in range(0, 3):
                my_mesh.vertices[i][j] = '{:.4f}'.format(my_mesh.vertices[i][j] * 0.0393701)
    elif convert == 'Meters':
        for i in range(len(my_mesh.vertices + 1)):
            for j in range(0, 3):
                my_mesh.vertices[i][j] = '{:.4f}'.format(my_mesh.vertices[i][j] / 1000)

    a = sorted(my_mesh.vertices, key=lambda k: [k[1], k[0], k[2]])
    b = np.array(a, np.int)  # b is the array of sorted vertices which prints in X, Z, Y
    if debug is True:
        print('Sorted Vertices:\n', b)
    # loop through the entire b array set max x = x, set max y = y if current x > max x, set max x = new x same with y
    maxX = 0
    maxY = 0
    for i in range(len(my_mesh.vertices)):
        if b[i][0] > maxX:
            maxX = b[i][0]
        if b[i][2] > maxY:
            maxY = b[i][2]
    if debug is True:
        print('X max: ', maxX, '\nY max:', maxY)
    #  generate domain of the building from the detected maximum values of X and Y
    domain = np.zeros([maxX, maxY])

    # initialize lists for vertices array loop
    xArray = [0] * len(b)
    yArray = [0] * len(b)
    zArray = [0] * len(b)

    for i in range(len(b)):
        if b[i][0] == maxX:
            xArray[i] = b[i][0] - 1
        else:
            xArray[i] = b[i][0]
        if b[i][2] == maxY:
            yArray[i] = b[i][2] - 1
        else:
            yArray[i] = b[i][2]
        zArray[i] = b[i][1]
    print('X Array:', xArray, '\nY Array:', yArray)
    domain[xArray, yArray] = zArray

    def countDigit(n):
        count = 0
        while n != 0:
            n //= 10
            count += 1
        return count

    def detect_z(vertices):
        z = []
        j = 0

        z.append(vertices[0][1])
        for i in range(len(vertices)):
            if vertices[i][1] != z[j]:
                z.append(vertices[i][1])
                j += 1
        return z

    Z = detect_z(b)

    max_digits = 0
    for i in range(len(Z)):
        if countDigit(Z[i]) > max_digits:
            max_digits = countDigit(Z[i])
    if debug is True:
        print('Array of Z values:', Z)
        print('Max number of digits:', max_digits)

    for k in range(len(Z)):
        for i in range(maxX):
            for j in range(maxY):
                point = [[i, Z[k], j]]
                (distances) = my_mesh.nearest.signed_distance(point)
                if distances >= 0:
                    domain[i][j] = f'{Z[k]:{max_digits + 1}.2f}'  # todo figure out formatting

    # Filps and rotates domain to correct orientation
    domain = np.fliplr(domain)
    domain = np.rot90(domain, 3)
    Ny = Ny - maxY
    Nx = Nx - maxX
    if Ny <= 0:
        sys.stderr.write('Ny not large enough! Must be at least ' + str(maxY))
        sys.exit()
    if Nx <= 0:
        sys.stderr.write('Nx not large enough! Must be at least ' + str(maxX))
        sys.exit()

    By = int(Ny / 2)
    Bx = int(Nx * 2/3)
    Ax = int(Nx * 1/3)
    building = np.pad(domain, [(By, By), (Bx, Ax)])

    building_Y = len(building)
    print(building_Y)
    building_X = maxX + Nx
    print(building_X)
    # ///////////////////// writes the completed topo file to a .txt file /////////////////////
    if write_to_file is True:
        with open(output + '_topo.txt', mode='w') as file:
            writer = csv.writer(file, delimiter=' ')

            for i in range(len(building)):
                writer.writerow(building[i, :])

        file.close()

    return


if __name__ == '__main__':
    #                 filename,     output name, convert, debug, write_to_file, Nx, Ny
    from_3d_generate('KD_mez.STL', 'KD_mez', 'Meters', True, True, 90, 120)
