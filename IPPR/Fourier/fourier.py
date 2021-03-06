# KhomZ


from http.client import FAILED_DEPENDENCY
from unittest import result
from cv2 import dft
from matplotlib.pyplot import get
from mysqlx import Row
import numpy as np
import pylab as py
from scipy import fftpack, misc
from PIL import Image
# from scipy.misc import lena


def dftmtx(N):
    '''Get Discrete fourier transform matrix of xize N x N.'''
    n = np.asmatrix(np.arange(N))
    return np.exp((-2j * np.pi / N) * n.T * n)


def idftmtx(N):
    '''Get inverse discrete fourier transform matrix of size N x N.'''
    n = np.asmatrix(np.arange(N))
    return np.exp((2j * np.pi / N) * n.T * n)


def fft(x):
    '''Vectorized & iterative FFT.'''
    x = np.asarray(x, dtype=complex)
    N = len(x)
    temp = x.reshape((1, N))

    while temp.shape[0] < N:
        m, n = temp.shape
        odd, even = temp[:, n / 2:], temp[:, :n / 2]
        coff = np.exp(-1j * np.pi * np.arange(m) / m)[:, None]
        temp = np.vstack((even + coff * odd, even - coff * odd))

    return temp.ravel()


def pow2_ceil(x):
    return 2 ** int(np.ceil(np.log2(x)))


def pad(data, P=None, Q=None):
    M, N = data.shape
    if not P:
        P, Q = pow2_ceil(M), pow2_ceil(N)

    temp = np.zeros((P, Q))
    temp[:M, :N] = data
    return temp


def get_2d(data, fn):
    '''Apply `fn` to each row, then to each column.'''
    result = np.copy(data)
    result = np.array([fn(row) for row in result])
    result = np.array([fn(col) for col in result.T])
    return result.T


def get_fft(data):
    if len(data.shape) == 1:
        return fft(data)
    return get_2d(data, fft)


def get_ifft(data):
    Fstar = np.conj(data)
    fstar = get_fft(Fstar) / reduce(np.multiply, data.shape, 1.0)
    return np.conj(fstar)


def get_dft(data):
    '''Get discrete fourier transform of data(numpy matrix/array).'''
    if len(data.shape)  == 1:
        return (dftmtx(len(data)) * data[:, None]).A1
    M,N = data.shape
    return np.asarray(dftmtx(M) * data * dftmtx(N))


def get_idft(data):
    '''Get inverse discrete fourier transform of data(numpy matrix/array).'''
    if len(data.shape) == 1:
        return (idftmtx(len(data)) * data[:, None] / len(data)).A1
    M, N = data.shape
    return np.asarray(idftmtx(M) * data * idftmtx(N) / (M * N))


def scale_intensity(f, typef=np.uint8, L=256):
    '''Scale the intensities in the matrix to [0, L-1].'''
    fm = f - np.min(f)
    fs = (L - 1) * (fm / np.max(fm))
    return typef(fs)


def shift_dft(f):
    '''Shift the fourier transform so that F(0,0) is in the center.'''
    y = np.asarray(f)  # copy
    for k, n in enumerate(f.shape):
        mid = (n + 1) / 2
        indices = np.concatenate((np.arange(mid, n), np.arange(mid)))
        y = np.take(y, indices, k)  # rearange each axes
    return y


def filter2(data, kernel):
    M, N = data.shape
    m, n = kernel.shape
    P, Q = s = (pow2_ceil(m + M - 1), pow2_ceil(n + N - 1))

    fpad = pad(data, P, Q)
    kpad = pad(np.flipud(np.fliplr(kernel)), P, Q)

    fpad[M:M + (m - 1) // 2, :N] = data[M - 1, :]
    fpad[:M, N:N + (n - 1) // 2] = data[:, N - 1].reshape((M, 1))

    xoff = m - (m - 1) // 2 - 1
    yoff = n - (n - 1) // 2 - 1
    fpad[P - xoff:, :N] = data[0, :]
    fpad[:M, Q - yoff:] = data[:, 0].reshape((M, 1))

    fpad[M:M + (m - 1) // 2, N:N + (n - 1) // 2] = data[-1, -1]
    fpad[P - xoff:, N:N + (n - 1) // 2] = data[0, -1]
    fpad[M:M + (m - 1) // 2, Q - yoff:] = data[-1, 0]
    fpad[P - xoff:, Q - yoff:] = data[0, 0]

    result = get_idft(get_dft(fpad) * get_dft(kpad))

    off = ((m - 1) // 2, (n - 1) // 2)
    result = result[off[0]:off[0] + M, off[1] + N]

    return result.real


def filter(data, kernel):
    M, N = data.shape
    P, Q = pow2_ceil(M), pow2_ceil(N)
    m, n = kernel.shape

    X, Y = np.meshgrid(np.arange(Q), np.arange(P))
    sign = np.power(-1, X + Y)

    fpad = np.zeros((P, Q))
    fpad[:M, :N] = data
    fpad = sign * fpad

    kpad = np.zeros((P, Q))
    kpad[:m, :n] = kernel

    fstar = get_dft(fpad)
    kstar = np.abs(shift_dft(get_dft(kpad)))
    return (get_idft(fstar * kstar).real * sign)[:M, :N]


def pad_then_crop(data, kernel, f):
    m, n = kernel.shape
    M, N = data.shape
    padded = np.lib.pad(data, (m,n), 'edge')
    return f(padded, kernel)[m:m+M, n:n+N]


def get_power_spectrum(input_img, transform=get_dft):
    '''Get the power spectrum image of a given image.'''
    data = np.reshape(input_img.getdata(), input_img.size[::-1])
    fourier = shift_dft(transform(data))
    outdata = scale_intensity(np.log(1 + np.abs(fourier)**2))
    return Image.fromarray(outdata)


def get_spectrum(input_img, transform=get_dft):
    '''Get the spectrum imgae of given image.'''
    data = np.reshape(input_img.getdata(), input_img.size[::-1])
    fourier = shift_dft(transform(data))
    outdata = scale_intensity(np.log(1 + np.abs(fourier)))
    return Image.fromarray(outdata)


def show():
    '''Show the power spectrum of lena.'''
    input_img = Image.fromarray(misc.lena())
    psd = get_power_spectrum(input_img)
    psd.show()


def check():
    # im = Image.open('a.png')
    im = Image.open('02.png')
    data = np.reshape(im.getdata(), im.size[::-1])
    kernel = np.full((11, 11), 1.0 / (11 * 11))
    result = pad_then_crop(data, kernel, filter)
    Image.fromarray(result).show()


def test(data, my_func, lib_func, all_right, name):
    '''Check if my implementation is close to the one in the library.'''
    my_result, lib_result = my_func(data), lib_func(data)
    error = np.abs(lib_result - my_result)
    error_range = (np.min(error), np.max(error))

    if all_right(lib_result, my_result):
        print('[PASSED] %s, '% name,)
        print('Error in (%.6e, %.6e)' % error_range)

    else:
        print("[FAILED] %s" %name)


if __name__ == "__main__":
    lena = np.reshape(misc.lena(), (1024, 256))
    data = np.random.rand(1024)

    test(lena, shift_dft, fftpack.fftshift, np.array_equal, 'Shift')
    test(lena, get_dft, fftpack.fft2, np.allclose, '2D-DFT')
    test(lena, get_idft, fftpack.ifft2, np.allclose, '2D-IDFT')
    test(lena, get_fft, fftpack.fft2, np.allclose, '2D-FFT')
    test(lena, get_ifft, fftpack.ifft2, np.allclose, '2D-IFFT')

    test(data, get_dft, fftpack.fft, np.allclose, '1D-DFT')
    test(data, get_idft, fftpack.ifft, np.allclose, '1D-IDFT')
    test(data, get_fft, fftpack.fft, np.allclose, '1D-FFT')
    test(data, get_ifft, fftpack.ifft, np.allclose, '1D-IFFT')

