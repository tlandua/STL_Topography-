import sys

import trimesh
import numpy as np
import csv
import time
from tqdm import tqdm
from icecream import ic
import io

import Sim_Create

global h
ic.configureOutput(prefix='Debug | ')


def prod_16(x):
    while x % 64 != 0:
        x += 1
    return x


def from_3d_generate(filename, output, convert, debug, write_to_file):
    my_mesh = trimesh.load(filename)
    debug = debug
    write_to_file = write_to_file
    t1 = time.perf_counter()
    try:
        if convert == 'Inches':
            for i in range(len(my_mesh.vertices + 1)):
                for j in range(0, 3):
                    my_mesh.vertices[i][j] = '{:.4f}'.format(my_mesh.vertices[i][j] * 0.0393701)
        elif convert == 'Meters':
            for i in range(len(my_mesh.vertices + 1)):
                for j in range(0, 3):
                    my_mesh.vertices[i][j] = '{:.4f}'.format(my_mesh.vertices[i][j] / 1000)
        elif convert == 'Kilometers':
            for i in range(len(my_mesh.vertices + 1)):
                for j in range(0, 3):
                    my_mesh.vertices[i][j] = '{:.4f}'.format(my_mesh.vertices[i][j] / 1000)
        elif convert == 'None':
            for i in range(len(my_mesh.vertices + 1)):
                for j in range(0, 3):
                    my_mesh.vertices[i][j] = '{:.4f}'.format(my_mesh.vertices[i][j])
    except:
        sys.stderr.write('Converting failed!')

    # ///////////////////// Sort and Convert Vertices /////////////////////
    a = sorted(my_mesh.vertices, key=lambda k: [k[1], k[0], k[2]])
    # Convert vertices to np array of integers
    Sorted = np.array(a, int)
    if debug is True:
        ic(Sorted)
    else:
        print('Vertices sorted. Enable debug to view.')

    # loop through the entire Sorted array set max x = x,
    # set max y = y if current x > max x, set max x = new x same with y
    minY = minX = maxX = maxY = 0
    for i in range(len(Sorted)):
        if Sorted[i][0] > maxX:
            maxX = Sorted[i][0]
        if Sorted[i][1] > maxY:
            maxY = Sorted[i][1]
    for i in range(len(Sorted)):
        if Sorted[i][0] < minX:
            minX = Sorted[i][0]
        if Sorted[i][1] < minY:
            minY = Sorted[i][1]

    if debug is True:
        ic(maxX, maxY)
    #  generate domain of the building from the detected maximum values of X and Y
    domain = np.zeros([maxX, maxY], dtype=int)

    # initialize lists for vertices array loop
    xArray = [0] * len(Sorted)
    yArray = [0] * len(Sorted)
    zArray = [0] * len(Sorted)

    for i in range(len(Sorted)):
        if Sorted[i][0] == maxX:
            xArray[i] = Sorted[i][0] - 1
        else:
            xArray[i] = Sorted[i][0]
        if Sorted[i][2] == maxY:
            yArray[i] = Sorted[i][1] - 1
        else:
            yArray[i] = Sorted[i][1]
        zArray[i] = Sorted[i][2]
    if debug is True:
        ic(xArray, yArray)
    else:
        print('Initial Domain Created. Enable debug to view.')
    # domain[xArray, yArray] = zArray

    # ///////////////////// Detect Unique Z Values /////////////////////
    def detect_z(vertices):  # Detect the unique values for Z
        global h
        z = []
        j = 0
        h = 0
        z.append(vertices[0][2])
        for i in range(len(vertices)):
            if vertices[i][2] > z[j]:
                z.append(int(vertices[i][2]))
                j += 1
            if z[j] > h:
                h = z[j]
        return z

    Z = detect_z(Sorted)
    ic(Z, len(Z), h)

    # ///////////////////// Setting grid point heights /////////////////////
    print('\033[93mInitiating Building Construction \033[0m')
    for k in tqdm(range(len(Z)), ncols=80, desc='Z loop', leave=True):
        for i in (range(maxX)):
            for j in (range(maxY)):
                point = [[i, j, Z[k]]]
                #  detect if grid point is within mesh
                (distances) = my_mesh.nearest.signed_distance(point)
                if distances >= 0:
                    domain[i][j] = Z[k]
    t2 = time.perf_counter()
    print(f'Building Construction Completed in {(t2 - t1):0.2f} seconds' if debug is True else "")

    # ///////////////////// Flips and rotates domain to correct orientation /////////////////////
    domain = np.fliplr(domain)
    # domain = np.rot90(domain, 4)

    # ///////////////////// Setting building domain /////////////////////
    try:
        #  create padding variables
        ss = int(4 * h)  # b
        temp = (ss*2) + maxX
        temp = prod_16(temp)
        temp = temp - maxX
        ss = round(temp/2)

        lu = int(4 * h)  # upstream
        ld = int(6 * h)  # downstream
        temp = lu + ld + maxY
        temp = prod_16(temp)
        temp = temp - maxY
        lu = round(temp*(1/3))
        ld = round(temp*(2/3))

        #  pad building
        building = np.pad(domain, [(int(ss), int(ss)), (int(lu), int(ld))])
        #  manual pad
        # building = np.pad(domain, [(84, 84), (61, 123)])

        building_Y = len(building)
        building_X = maxY + lu + ld
        # building_X = maxY + 61 + 123
        print('Total domain in Y: ', building_Y)
        print('Total domain in X: ', building_X)
    except:
        sys.stderr.write('Something went wrong with building padding')
        building = []
        building_X = building_Y = 0

    # ///////////////////// writes the completed topo file to a .txt file /////////////////////
    if write_to_file is True:
        with io.open(output, mode='w', newline='\r') as file:
            writer = csv.writer(file, delimiter=' ', lineterminator='\r')

            for i in range(len(building)):
                writer.writerow(building[i, :])
        Sim_Create.simulate()

        file.close()
    t3 = time.perf_counter()
    print(f'All Processes Completed in {(t3 - t1):0.2f} seconds' if debug is True else "")
    #  Adding coloring for the print status of debug and write to file
    if debug is True:
        d = '\033[92mTrue\033[0m'
    else:
        d = '\033[91mFalse\033[0m'
    if write_to_file is True:
        w = '\033[92mTrue\033[0m'
    else:
        w = '\033[91mFalse\033[0m'
    #  Final print indicating selections and filename
    print('Topography file named \033[92m' + output + '\033[0m was processed. For this run, debug was ' + d,
          ', and write to file was ' + w)
    grd = [building_X, building_Y, h]
    return grd


if __name__ == '__main__':
    #                 filename,     output name, convert, debug, write_to_file
    from_3d_generate('stadium_and_misc.STL', 'stadium_and_misc_topo', 'None', True, True)
