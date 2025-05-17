import React, { useRef, useState } from 'react';
import Webcam from 'react-webcam';
import axios from 'axios';

function Login() {
  const webcamRef = useRef(null);
  const [username, setUsername] = useState('');
  const [capturedImage, setCapturedImage] = useState(null);

  const capture = () => {
    const imageSrc = webcamRef.current.getScreenshot();
    setCapturedImage(imageSrc);
  };

  const loginUser = async () => {
    const blob = await (await fetch(capturedImage)).blob();
    const file = new File([blob], 'face.jpg', { type: 'image/jpeg' });

    const formData = new FormData();
    formData.append('username', username);
    formData.append('image', file);

    try {
      const res = await axios.post('http://localhost:5000/api/login', formData);
      alert('Login successful! Token: ' + res.data.token);
      localStorage.setItem('token', res.data.token);
      window.location.href = '/dashboard';
    } catch (err) {
      console.error(err);
      alert('Login failed');
    }
  };

  return (
    <div>
      <h2>Login</h2>
      <input placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
      <Webcam ref={webcamRef} screenshotFormat="image/jpeg" />
      <button onClick={capture}>Capture</button>
      {capturedImage && <img src={capturedImage} alt="Captured" />}
      <button onClick={loginUser}>Login</button>
    </div>
  );
}

export default Login;
