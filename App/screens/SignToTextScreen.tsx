import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  StatusBar,
  SafeAreaView,
  Dimensions,
} from 'react-native';
import { CameraView, useCameraPermissions, PermissionResponse } from 'expo-camera';
import { Video, ResizeMode } from 'expo-av';
import { Ionicons } from '@expo/vector-icons';
import { Audio } from 'expo-av';

// API configuration
const API_URL = 'http://192.168.29.233:5000'; // For Android emulator

const { width, height } = Dimensions.get('window');

const SignToTextScreen = () => {
  const [cameraPermission, requestCameraPermission] = useCameraPermissions();
  const [micPermission, setMicPermission] = useState<boolean | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedVideo, setRecordedVideo] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [isFrontCamera, setIsFrontCamera] = useState(false);
  const [isTranslating, setIsTranslating] = useState(false);
  const [translationResult, setTranslationResult] = useState<string | null>(null);
  const [lastUploadId, setLastUploadId] = useState<string | null>(null);
  const cameraRef = useRef<any>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Request microphone permission
  useEffect(() => {
    const requestMicPermission = async () => {
      try {
        const { status } = await Audio.requestPermissionsAsync();
        setMicPermission(status === 'granted');
        if (status !== 'granted') {
          Alert.alert(
            'Microphone Permission',
            'We need microphone access to record videos with audio. Please grant permission in your device settings.'
          );
        }
      } catch (error) {
        console.error('Error requesting microphone permission:', error);
        setMicPermission(false);
      }
    };
    
    requestMicPermission();
    
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  const startRecording = async () => {
    if (!cameraPermission?.granted || !micPermission) {
      Alert.alert(
        'Permissions Required',
        'Camera and microphone permissions are required to record video.',
        [
          { text: 'Cancel', style: 'cancel' },
          { 
            text: 'Grant Permissions', 
            onPress: async () => {
              await requestCameraPermission();
              const { status } = await Audio.requestPermissionsAsync();
              setMicPermission(status === 'granted');
            } 
          }
        ]
      );
      return;
    }

    if (cameraRef.current) {
      try {
        setIsRecording(true);
        const video = await cameraRef.current.recordAsync();
        setRecordedVideo(video.uri);
      } catch (error) {
        console.error('Error recording video:', error);
        Alert.alert('Error', 'Failed to record video');
      } finally {
        setIsRecording(false);
      }
    }
  };

  const stopRecording = () => {
    if (cameraRef.current) {
      cameraRef.current.stopRecording();
    }
  };

  const flipCamera = () => {
    setIsFrontCamera(prev => !prev);
  };

  const resetRecording = () => {
    setRecordedVideo(null);
    setTranslationResult(null);
    setLastUploadId(null);
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  };

  const startPollingForResults = (uploadId: string) => {
    setIsTranslating(true);
    setLastUploadId(uploadId);
    
    // Poll the server every 2 seconds to check for translation results
    pollingIntervalRef.current = setInterval(async () => {
      try {
        const response = await fetch(`${API_URL}/latest-translation`);
        const data = await response.json();
        
        // If we have a result and it matches our upload ID
        if (data.video_id === uploadId && data.text) {
          setTranslationResult(data.text);
          setIsTranslating(false);
          
          // Stop polling once we have our result
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
        }
      } catch (error) {
        console.error('Error polling for translation:', error);
      }
    }, 2000);
    
    // Set a timeout to stop polling after 30 seconds
    setTimeout(() => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
        
        // If we still don't have a result, show an error
        if (isTranslating) {
          setIsTranslating(false);
          Alert.alert('Translation Error', 'Could not get translation results. Please try again.');
        }
      }
    }, 30000);
  };

  const uploadToCloudinary = async () => {
    if (!recordedVideo) {
      Alert.alert('Error', 'No video to upload');
      return;
    }

    try {
      setUploading(true);
      setTranslationResult(null);
      
      const formData = new FormData();
      const fileName = `sign_${Date.now()}`;
      
      // Add folder parameter to store in sign-to-text folder
      formData.append('file', {
        uri: recordedVideo,
        type: 'video/mp4',
        name: 'video.mp4',
      } as any);
      formData.append('upload_preset', 'video_upload');
      formData.append('cloud_name', 'dzouwixsp');
      formData.append('public_id', fileName);
      formData.append('folder', 'sign-to-text');
      
      console.log('Uploading video to sign-to-text folder:', fileName);

      const response = await fetch(
        'https://api.cloudinary.com/v1_1/dzouwixsp/video/upload',
        {
          method: 'POST',
          body: formData,
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      const data = await response.json();
      console.log('Upload response:', data);
      
      if (data && data.public_id) {
        // Start polling for translation results with the complete public_id including folder
        startPollingForResults(data.public_id);
      } else {
        Alert.alert('Error', 'Failed to get video ID from upload');
      }
    } catch (error) {
      console.error('Error uploading video:', error);
      Alert.alert('Error', 'Failed to upload video');
      setIsTranslating(false);
    } finally {
      setUploading(false);
    }
  };

  if (!cameraPermission) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar backgroundColor="#000" barStyle="light-content" />
        <ActivityIndicator size="large" color="#4F8EF7" />
      </SafeAreaView>
    );
  }

  if (!cameraPermission.granted || micPermission === false) {
    return (
      <SafeAreaView style={styles.permissionContainer}>
        <StatusBar backgroundColor="#000" barStyle="light-content" />
        <Ionicons name="camera-outline" size={80} color="#4F8EF7" />
        <Text style={styles.permissionTitle}>Permissions Required</Text>
        <Text style={styles.permissionText}>
          We need camera and microphone access to record videos. Please grant permissions to continue.
        </Text>
        <TouchableOpacity
          style={styles.permissionButton}
          onPress={async () => {
            await requestCameraPermission();
            const { status } = await Audio.requestPermissionsAsync();
            setMicPermission(status === 'granted');
          }}
        >
          <Text style={styles.permissionButtonText}>Grant Permissions</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar backgroundColor="#000" barStyle="light-content" />
      {!recordedVideo ? (
        <>
          <CameraView
            style={styles.camera}
            ref={cameraRef}
            facing={isFrontCamera ? "front" : "back"}
            mode="video"
          >
            <View style={styles.overlay}>
              {isRecording && (
                <View style={styles.recordingIndicator}>
                  <View style={styles.recordingDot} />
                  <Text style={styles.recordingText}>RECORDING</Text>
                </View>
              )}
              
              <View style={styles.topControls}>
                <TouchableOpacity 
                  style={styles.iconButton}
                  onPress={flipCamera}
                >
                  <Ionicons name="camera-reverse-outline" size={28} color="#fff" />
                </TouchableOpacity>
              </View>
              
              <View style={styles.bottomControls}>
                <TouchableOpacity
                  style={[styles.recordButton, isRecording && styles.recordingButton]}
                  onPress={isRecording ? stopRecording : startRecording}
                >
                  <View style={isRecording ? styles.stopIcon : styles.recordIcon} />
                </TouchableOpacity>
              </View>
            </View>
          </CameraView>
        </>
      ) : (
        <View style={styles.previewContainer}>
          <View style={styles.videoHeader}>
            <TouchableOpacity
              style={styles.backButton}
              onPress={resetRecording}
            >
              <Ionicons name="arrow-back" size={24} color="#fff" />
            </TouchableOpacity>
            <Text style={styles.previewTitle}>Video Preview</Text>
            <View style={{ width: 24 }} />
          </View>
          
          <Video
            source={{ uri: recordedVideo }}
            style={styles.video}
            useNativeControls
            resizeMode={ResizeMode.CONTAIN}
          />
          
          {isTranslating ? (
            <View style={styles.translatingContainer}>
              <ActivityIndicator size="large" color="#4F8EF7" />
              <Text style={styles.translatingText}>Translating Sign Language...</Text>
            </View>
          ) : translationResult ? (
            <View style={styles.resultContainer}>
              <Text style={styles.resultLabel}>Translation:</Text>
              <Text style={styles.resultText}>{translationResult}</Text>
              <TouchableOpacity
                style={styles.newRecordingButton}
                onPress={resetRecording}
              >
                <Text style={styles.actionButtonText}>New Recording</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <View style={styles.actionButtons}>
              <TouchableOpacity
                style={[styles.actionButton, styles.discardButton]}
                onPress={resetRecording}
              >
                <Ionicons name="refresh-outline" size={22} color="#fff" />
                <Text style={styles.actionButtonText}>Retake</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[styles.actionButton, styles.uploadButton, uploading && styles.uploadingButton]}
                onPress={uploadToCloudinary}
                disabled={uploading || isTranslating}
              >
                {uploading ? (
                  <ActivityIndicator size="small" color="#fff" />
                ) : (
                  <>
                    <Ionicons name="cloud-upload-outline" size={22} color="#fff" />
                    <Text style={styles.actionButtonText}>Upload</Text>
                  </>
                )}
              </TouchableOpacity>
            </View>
          )}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  permissionContainer: {
    flex: 1,
    backgroundColor: '#121212',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  permissionTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
    marginTop: 20,
    marginBottom: 10,
  },
  permissionText: {
    fontSize: 16,
    color: '#ccc',
    textAlign: 'center',
    marginBottom: 30,
  },
  permissionButton: {
    backgroundColor: '#4F8EF7',
    paddingVertical: 12,
    paddingHorizontal: 40,
    borderRadius: 30,
  },
  permissionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  camera: {
    flex: 1,
  },
  overlay: {
    flex: 1,
    flexDirection: 'column',
    justifyContent: 'space-between',
  },
  topControls: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    padding: 20,
    marginTop: 30,
  },
  iconButton: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: 'rgba(0,0,0,0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  bottomControls: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingBottom: 40,
  },
  recordButton: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 4,
    borderColor: '#fff',
  },
  recordingButton: {
    backgroundColor: 'rgba(255, 70, 70, 0.3)',
    borderColor: '#FF4646',
  },
  recordIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#FF4646',
  },
  stopIcon: {
    width: 24,
    height: 24,
    backgroundColor: '#FF4646',
  },
  recordingIndicator: {
    position: 'absolute',
    top: 60,
    alignSelf: 'center',
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    borderRadius: 20,
    paddingHorizontal: 15,
    paddingVertical: 8,
  },
  recordingDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#FF4646',
    marginRight: 8,
  },
  recordingText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  previewContainer: {
    flex: 1,
    backgroundColor: '#121212',
  },
  videoHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 50,
    paddingHorizontal: 20,
    paddingBottom: 15,
    backgroundColor: '#000',
  },
  backButton: {
    padding: 5,
  },
  previewTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  video: {
    width: '100%',
    height: height * 0.5,
    backgroundColor: '#000',
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 30,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 25,
    borderRadius: 25,
    minWidth: 130,
    justifyContent: 'center',
  },
  discardButton: {
    backgroundColor: '#555',
  },
  uploadButton: {
    backgroundColor: '#4F8EF7',
  },
  uploadingButton: {
    backgroundColor: '#3A6CBC',
  },
  actionButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    marginLeft: 8,
    fontSize: 16,
  },
  translatingContainer: {
    padding: 30,
    alignItems: 'center',
    justifyContent: 'center',
  },
  translatingText: {
    color: '#fff',
    fontSize: 16,
    marginTop: 15,
    textAlign: 'center',
  },
  resultContainer: {
    padding: 30,
    alignItems: 'center',
  },
  resultLabel: {
    color: '#999',
    fontSize: 16,
    marginBottom: 10,
  },
  resultText: {
    color: '#fff',
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 30,
  },
  newRecordingButton: {
    backgroundColor: '#4F8EF7',
    paddingVertical: 12,
    paddingHorizontal: 25,
    borderRadius: 25,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
});

export default SignToTextScreen; 