import React, { useRef, useState } from 'react';
import Webcam from 'react-webcam';
import axios from 'axios';

function Register() {
  const webcamRef = useRef(null);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [capturedImage, setCapturedImage] = useState(null);

  const capture = () => {
    const imageSrc = webcamRef.current.getScreenshot();
    setCapturedImage(imageSrc);
  };

  const registerUser = async () => {
    const blob = await (await fetch(capturedImage)).blob();
    const file = new File([blob], 'face.jpg', { type: 'image/jpeg' });

    const formData = new FormData();
    formData.append('username', username);
    formData.append('email', email);
    formData.append('image', file);

    try {
      const res = await axios.post('http://localhost:5000/api/register', formData);
      alert('Registered! Token: ' + res.data.token);
    } catch (err) {
      console.error(err);
      alert('Registration failed');
    }
  };

  return (
    <div>
      <h2>Register</h2>
      <input placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
      <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
      <Webcam ref={webcamRef} screenshotFormat="image/jpeg" />
      <button onClick={capture}>Capture</button>
      {capturedImage && <img src={capturedImage} alt="Captured" />}
      <button onClick={registerUser}>Register</button>
    </div>
  );
}

export default Register;
