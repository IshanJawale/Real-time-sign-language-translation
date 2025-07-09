import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  SafeAreaView,
  Image,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { ResizeMode, Video } from 'expo-av';
import { useNavigation } from '@react-navigation/native';
import axios from 'axios';

const API_URL = 'http://192.168.29.233:5000'; // For Android emulator

const TextToSignScreen = () => {
  const [inputText, setInputText] = useState('');
  const [isConverting, setIsConverting] = useState(false);
  const [result, setResult] = useState<null | { videoUrl: string, publicId: string }>(null);
  const [error, setError] = useState<string | null>(null);
  const navigation = useNavigation();

  const commonPhrases = [
    'Hello',
    'Thank you',
    'How are you?',
    'My name is',
    'Nice to meet you',
    'Help me please',
    'I understand',
    'I don\'t understand',
  ];

  const convertTextToSign = async () => {
    if (!inputText.trim()) {
      return;
    }

    setIsConverting(true);
    setError(null);
    
    try {
      // Call the Flask server to convert text to sign
      const response = await axios.post(`${API_URL}/text-to-sign`, {
        text: inputText.trim()
      });
      
      if (response.data.status === 'success') {
        setResult({
          videoUrl: response.data.video_url,
          publicId: response.data.public_id
        });
      } else {
        setError('Failed to convert text to sign language');
      }
    } catch (error) {
      console.error('Error converting text to sign:', error);
      setError('An error occurred while converting text to sign language');
    } finally {
      setIsConverting(false);
    }
  };

  const selectPhrase = (phrase: string) => {
    setInputText(phrase);
  };

  const clearText = () => {
    setInputText('');
    setResult(null);
    setError(null);
  };

  const handleDone = async () => {
    // If there's a video, delete it from Cloudinary
    if (result && result.publicId) {
      try {
        console.log('Deleting video with public_id:', result.publicId);
        // The publicId returned by Cloudinary already includes the folder path
        await axios.post(`${API_URL}/delete-cloudinary-resource`, {
          public_id: result.publicId,
          resource_type: 'video'
        });
      } catch (error) {
        console.error('Error deleting resource from Cloudinary:', error);
      }
    }
    
    // Navigate back to home screen
    navigation.navigate('Home' as never);
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.inputContainer}>
          <Text style={styles.label}>Enter Text to Convert</Text>
          <View style={styles.textInputWrapper}>
            <TextInput
              style={styles.input}
              value={inputText}
              onChangeText={setInputText}
              placeholder="Type text to translate to sign language..."
              placeholderTextColor="#888"
              multiline
              maxLength={100}
            />
            {inputText.length > 0 && (
              <TouchableOpacity onPress={clearText} style={styles.clearButton}>
                <Ionicons name="close-circle" size={20} color="#888" />
              </TouchableOpacity>
            )}
          </View>
          <Text style={styles.charCounter}>{inputText.length}/100</Text>
        </View>

        <Text style={styles.sectionTitle}>Common Phrases</Text>
        <View style={styles.phrasesContainer}>
          {commonPhrases.map((phrase, index) => (
            <TouchableOpacity
              key={index}
              style={styles.phraseButton}
              onPress={() => selectPhrase(phrase)}
            >
              <Text style={styles.phraseText}>{phrase}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <TouchableOpacity
          style={[
            styles.convertButton,
            (!inputText.trim() || isConverting) && styles.disabledButton
          ]}
          onPress={convertTextToSign}
          disabled={!inputText.trim() || isConverting}
        >
          {isConverting ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <>
              <Ionicons name="language-outline" size={24} color="#fff" />
              <Text style={styles.convertButtonText}>Convert to Sign Language</Text>
            </>
          )}
        </TouchableOpacity>

        {error && (
          <View style={styles.errorContainer}>
            <Ionicons name="alert-circle" size={24} color="#FF6B6B" />
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {isConverting && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#4F8EF7" />
            <Text style={styles.loadingText}>Generating sign language video...</Text>
          </View>
        )}

        {result && (
          <View style={styles.resultContainer}>
            <Text style={styles.resultTitle}>Sign Language Translation</Text>
            <View style={styles.videoContainer}>
              <Video
                source={{ uri: result.videoUrl }}
                rate={1.0}
                volume={1.0}
                isMuted={false}
                resizeMode={ResizeMode.CONTAIN}
                shouldPlay
                isLooping
                style={styles.video}
                useNativeControls
              />
            </View>

            <TouchableOpacity
              style={styles.doneButton}
              onPress={handleDone}
            >
              <Ionicons name="checkmark-circle" size={24} color="#fff" />
              <Text style={styles.doneButtonText}>Done</Text>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121212',
  },
  scrollContent: {
    padding: 20,
  },
  inputContainer: {
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  textInputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1e1e1e',
    borderRadius: 10,
    paddingHorizontal: 15,
  },
  input: {
    flex: 1,
    height: 100,
    color: '#fff',
    fontSize: 16,
    textAlignVertical: 'top',
    paddingTop: 15,
  },
  clearButton: {
    padding: 5,
  },
  charCounter: {
    color: '#888',
    fontSize: 12,
    textAlign: 'right',
    marginTop: 5,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 10,
  },
  phrasesContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 20,
  },
  phraseButton: {
    backgroundColor: '#2a2a2a',
    borderRadius: 20,
    paddingHorizontal: 15,
    paddingVertical: 8,
    margin: 5,
  },
  phraseText: {
    color: '#fff',
    fontSize: 14,
  },
  convertButton: {
    backgroundColor: '#4F8EF7',
    borderRadius: 10,
    padding: 15,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  disabledButton: {
    backgroundColor: '#2a3c5c',
    opacity: 0.7,
  },
  convertButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 10,
  },
  resultContainer: {
    backgroundColor: '#1e1e1e',
    borderRadius: 10,
    padding: 15,
    marginBottom: 20,
  },
  resultTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  videoContainer: {
    height: 250,
    borderRadius: 10,
    overflow: 'hidden',
    marginBottom: 15,
    backgroundColor: '#2a2a2a',
  },
  video: {
    width: '100%',
    height: '100%',
  },
  errorContainer: {
    backgroundColor: '#2a2020',
    borderRadius: 10,
    padding: 15,
    marginBottom: 20,
    flexDirection: 'row',
    alignItems: 'center',
  },
  errorText: {
    color: '#FF6B6B',
    marginLeft: 10,
    fontSize: 14,
  },
  loadingContainer: {
    padding: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    color: '#fff',
    marginTop: 10,
    fontSize: 14,
  },
  doneButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 10,
    padding: 15,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  doneButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 10,
  },
});

export default TextToSignScreen; 