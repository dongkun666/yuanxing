import React from 'react';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import {createNativeStackNavigator} from '@react-navigation/native-stack';
import {useSelector} from 'react-redux';
import Icon from 'react-native-vector-icons/Ionicons';

import HomeScreen from '../screens/HomeScreen';
import CasesScreen from '../screens/CasesScreen';
import CaseDetailScreen from '../screens/CaseDetailScreen';
import ContractReviewScreen from '../screens/ContractReviewScreen';
import ProfileScreen from '../screens/ProfileScreen';
import LoginScreen from '../screens/LoginScreen';
import ScheduleScreen from '../screens/ScheduleScreen';
import AIChatScreen from '../screens/AIChatScreen';
import {COLORS} from '../theme';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

const HomeStack = () => (
  <Stack.Navigator screenOptions={{headerShown: false}}>
    <Stack.Screen name="HomeMain" component={HomeScreen} />
    <Stack.Screen name="CaseDetail" component={CaseDetailScreen} />
    <Stack.Screen name="Schedule" component={ScheduleScreen} />
    <Stack.Screen name="AIChat" component={AIChatScreen} />
  </Stack.Navigator>
);

const CasesStack = () => (
  <Stack.Navigator screenOptions={{headerShown: false}}>
    <Stack.Screen name="CasesList" component={CasesScreen} />
    <Stack.Screen name="CaseDetail" component={CaseDetailScreen} />
  </Stack.Navigator>
);

const ContractStack = () => (
  <Stack.Navigator screenOptions={{headerShown: false}}>
    <Stack.Screen name="ContractReviewMain" component={ContractReviewScreen} />
  </Stack.Navigator>
);

const ProfileStack = () => (
  <Stack.Navigator screenOptions={{headerShown: false}}>
    <Stack.Screen name="ProfileMain" component={ProfileScreen} />
    <Stack.Screen name="Login" component={LoginScreen} />
  </Stack.Navigator>
);

const TabNavigator = () => (
  <Tab.Navigator
    screenOptions={({route}) => ({
      tabBarIcon: ({focused, color, size}) => {
        let iconName;
        switch (route.name) {
          case 'Home':
            iconName = focused ? 'home' : 'home-outline';
            break;
          case 'Cases':
            iconName = focused ? 'book' : 'book-outline';
            break;
          case 'Contract':
            iconName = focused ? 'document-text' : 'document-text-outline';
            break;
          case 'Profile':
            iconName = focused ? 'person' : 'person-outline';
            break;
          default:
            iconName = 'help';
        }
        return <Icon name={iconName} size={size} color={color} />;
      },
      tabBarActiveTintColor: COLORS.light.primary,
      tabBarInactiveTintColor: COLORS.light.textLight,
      tabBarStyle: {
        backgroundColor: COLORS.light.surface,
        borderTopColor: COLORS.light.borderLight,
        paddingBottom: 5,
        paddingTop: 5,
        height: 60,
      },
      tabBarLabelStyle: {
        fontSize: 12,
        fontWeight: '500',
      },
      headerShown: false,
    })}>
    <Tab.Screen name="Home" component={HomeStack} options={{title: '首页'}} />
    <Tab.Screen name="Cases" component={CasesStack} options={{title: '判例'}} />
    <Tab.Screen name="Contract" component={ContractStack} options={{title: '合同审查'}} />
    <Tab.Screen name="Profile" component={ProfileStack} options={{title: '我的'}} />
  </Tab.Navigator>
);

const AppNavigator = () => {
  const {isAuthenticated} = useSelector(state => state.auth);

  return (
    <Stack.Navigator screenOptions={{headerShown: false}}>
      {isAuthenticated ? (
        <Stack.Screen name="MainTabs" component={TabNavigator} />
      ) : (
        <Stack.Screen name="Login" component={LoginScreen} />
      )}
    </Stack.Navigator>
  );
};

export default AppNavigator;
