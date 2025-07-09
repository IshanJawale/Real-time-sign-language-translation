import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  SafeAreaView,
  StatusBar,
  Image,
  Dimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';

const { width } = Dimensions.get('window');
const cardWidth = width * 0.8;

const HomeScreen = () => {
  const navigation = useNavigation();

  const infoCards = [
    {
      id: 1,
      title: 'Sign Language Recognition',
      description: 'Use the camera to capture sign language gestures and convert them to text.',
      icon: 'hand-left-outline',
    },
    {
      id: 2,
      title: 'Text to Sign',
      description: 'Convert text into corresponding sign language animations.',
      icon: 'text-outline',
    },
    {
      id: 3,
      title: 'Real-time Translation',
      description: 'Get instant translation of sign language to text and vice versa.',
      icon: 'sync-outline',
    },
  ];

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar backgroundColor="#121212" barStyle="light-content" />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Realtime Sign Language</Text>
        <Text style={styles.subtitle}>Breaking communication barriers</Text>
      </View>

      {/* Info Cards */}
      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.cardsContainer}
        snapToInterval={cardWidth + 20}
        decelerationRate="fast"
        pagingEnabled
      >
        {infoCards.map(card => (
          <View key={card.id} style={styles.card}>
            <Ionicons name={card.icon} size={48} color="#4F8EF7" />
            <Text style={styles.cardTitle}>{card.title}</Text>
            <Text style={styles.cardDescription}>{card.description}</Text>
          </View>
        ))}
      </ScrollView>

      {/* Action Buttons */}
      <View style={styles.actionsContainer}>
        <TouchableOpacity 
          style={[styles.actionButton, styles.signToTextButton]} 
          onPress={() => navigation.navigate('SignToText')}
        >
          <Ionicons name="videocam-outline" size={24} color="#fff" />
          <Text style={styles.actionButtonText}>Sign to Text</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.actionButton, styles.textToSignButton]}
          onPress={() => navigation.navigate('TextToSign')}
        >
          <Ionicons name="chatbubble-outline" size={24} color="#fff" />
          <Text style={styles.actionButtonText}>Text to Sign</Text>
        </TouchableOpacity>
      </View>

      {/* Bottom Info */}
      <View style={styles.footer}>
        <Text style={styles.footerText}>
          Created with ❤️ for the deaf community
        </Text>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121212',
  },
  header: {
    paddingTop: 60,
    paddingBottom: 20,
    paddingHorizontal: 20,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#aaa',
  },
  cardsContainer: {
    paddingHorizontal: 10,
    paddingVertical: 20,
  },
  card: {
    width: cardWidth,
    backgroundColor: '#1e1e1e',
    borderRadius: 15,
    padding: 20,
    marginHorizontal: 10,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
    alignItems: 'center',
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginVertical: 10,
    textAlign: 'center',
  },
  cardDescription: {
    fontSize: 14,
    color: '#bbb',
    textAlign: 'center',
    lineHeight: 20,
  },
  actionsContainer: {
    paddingHorizontal: 20,
    paddingVertical: 20,
    alignItems: 'center',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
  },
  signToTextButton: {
    backgroundColor: '#4F8EF7',
  },
  textToSignButton: {
    backgroundColor: '#FF6B6B',
  },
  actionButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginLeft: 10,
  },
  footer: {
    padding: 20,
    alignItems: 'center',
  },
  footerText: {
    color: '#777',
    fontSize: 14,
  },
});

export default HomeScreen; 