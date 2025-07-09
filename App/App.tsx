import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar, View, Image, StyleSheet, ActivityIndicator } from 'react-native';
import HomeScreen from './screens/HomeScreen';
import SignToTextScreen from './screens/SignToTextScreen';
import TextToSignScreen from './screens/TextToSignScreen';

const Stack = createNativeStackNavigator();

export default function App() {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate some loading time
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 2000);

    return () => clearTimeout(timer);
  }, []);

  if (isLoading) {
    return (
      <View style={styles.splashContainer}>
        <StatusBar backgroundColor="#121212" barStyle="light-content" />
        <Image 
          source={{ uri: 'https://api.a0.dev/assets/image?text=minimal%20sign%20language%20logo%20black%20and%20white&aspect=1:1' }}
          style={styles.splashImage}
          resizeMode="contain"
        />
        <ActivityIndicator 
          size="large" 
          color="#4F8EF7" 
          style={styles.loader}
        />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <StatusBar backgroundColor="#000" barStyle="light-content" />
      <Stack.Navigator 
        initialRouteName="Home"
        screenOptions={{
          headerStyle: {
            backgroundColor: '#121212',
          },
          headerTintColor: '#fff',
          headerTitleStyle: {
            fontWeight: 'bold',
          },
          contentStyle: {
            backgroundColor: '#000',
          }
        }}
      >
        <Stack.Screen 
          name="Home" 
          component={HomeScreen} 
          options={{ 
            title: "Sign Language Translator",
            headerShown: false, 
          }} 
        />
        <Stack.Screen 
          name="SignToText" 
          component={SignToTextScreen} 
          options={{ 
            title: "Sign to Text",
            headerTitleAlign: 'center',
          }} 
        />
        <Stack.Screen 
          name="TextToSign" 
          component={TextToSignScreen}
          options={{ 
            title: "Text to Sign",
            headerTitleAlign: 'center', 
          }} 
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  splashContainer: {
    flex: 1,
    backgroundColor: '#000000',
    alignItems: 'center',
    justifyContent: 'center',
  },
  splashImage: {
    width: 250,
    height: 250,
    backgroundColor: '#121212',
  },
  loader: {
    marginTop: 20,
  }
});
