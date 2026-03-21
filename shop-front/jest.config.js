/** @type {import('@jest/types').Config.InitialOptions} */
const config = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
    '\\.(css|less|scss|sass)$': '<rootDir>/__mocks__/styleMock.js',
    '^next/link$': '<rootDir>/__mocks__/nextLink.tsx',
    '^next/image$': '<rootDir>/__mocks__/nextImage.tsx',
    '^@radix-ui/react-toast$': '<rootDir>/__mocks__/radixToast.tsx',
  },
  testMatch: ['**/__tests__/**/*.{ts,tsx}', '**/*.{spec,test}.{ts,tsx}'],
  transform: {
    '^.+\\.(ts|tsx)$': ['ts-jest', {
      tsconfig: {
        jsx: 'react-jsx',
      },
    }],
  },
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],
  collectCoverageFrom: [
    'app/**/*.{ts,tsx}',
    'components/**/*.{ts,tsx}',
    'lib/**/*.{ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
  ],
}

module.exports = config
