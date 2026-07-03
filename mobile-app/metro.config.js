const {getDefaultConfig, mergeConfig} = require('@react-native/metro-config');

const config = {
  transformer: {
    getTransformOptions: async () => ({
      transform: {
        experimentalImportSupport: false,
        inlineRequires: true,
      },
    }),
  },
  resolver: {
    assetExts: ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'],
    sourceExts: ['jsx', 'js', 'ts', 'tsx'],
  },
};

module.exports = mergeConfig(getDefaultConfig(__dirname), config);
