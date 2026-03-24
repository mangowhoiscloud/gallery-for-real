import type { Config } from 'jest'

const config: Config = {
  testEnvironment: 'jsdom',
  transform: {
    '^.+\\.tsx?$': ['ts-jest', {
      tsconfig: {
        jsx: 'react-jsx',
        moduleResolution: 'node',
        allowJs: true,
      },
    }],
  },
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
    '\\.(css|less|scss|sass)$': '<rootDir>/__mocks__/fileMock.js',
    '^next/font/(.*)$': '<rootDir>/__mocks__/next-font-mock.js',
  },
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
}

export default config
