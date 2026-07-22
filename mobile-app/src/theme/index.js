export const COLORS = {
  light: {
    primary: '#1e40af',
    primaryLight: '#3b82f6',
    primaryDark: '#1e3a8a',
    secondary: '#64748b',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#06b6d4',
    background: '#f8fafc',
    surface: '#ffffff',
    text: '#1e293b',
    textSecondary: '#64748b',
    textLight: '#94a3b8',
    border: '#e2e8f0',
    borderLight: '#f1f5f9',
    card: '#ffffff',
    shadow: 'rgba(0, 0, 0, 0.06)',
  },
  dark: {
    primary: '#3b82f6',
    primaryLight: '#60a5fa',
    primaryDark: '#1d4ed8',
    secondary: '#94a3b8',
    success: '#34d399',
    warning: '#fbbf24',
    danger: '#f87171',
    info: '#22d3ee',
    background: '#0f172a',
    surface: '#1e293b',
    text: '#f1f5f9',
    textSecondary: '#94a3b8',
    textLight: '#64748b',
    border: '#334155',
    borderLight: '#1e293b',
    card: '#1e293b',
    shadow: 'rgba(0, 0, 0, 0.3)',
  },
};

export const SIZES = {
  base: 8,
  font: 14,
  radius: 12,
  padding: 24,
  h1: 32,
  h2: 28,
  h3: 24,
  h4: 20,
  body1: 16,
  body2: 14,
  caption: 12,
  small: 11,
};

export const FONTS = {
  h1: {fontSize: SIZES.h1, fontWeight: '700'},
  h2: {fontSize: SIZES.h2, fontWeight: '700'},
  h3: {fontSize: SIZES.h3, fontWeight: '600'},
  h4: {fontSize: SIZES.h4, fontWeight: '600'},
  body1: {fontSize: SIZES.body1, fontWeight: '400'},
  body2: {fontSize: SIZES.body2, fontWeight: '400'},
  caption: {fontSize: SIZES.caption, fontWeight: '400'},
  bold: {fontWeight: '700'},
  semiBold: {fontWeight: '600'},
};

export const SHADOWS = {
  small: {
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  medium: {
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 4},
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 4,
  },
  large: {
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 8},
    shadowOpacity: 0.15,
    shadowRadius: 24,
    elevation: 8,
  },
};

export default {COLORS, SIZES, FONTS, SHADOWS};
