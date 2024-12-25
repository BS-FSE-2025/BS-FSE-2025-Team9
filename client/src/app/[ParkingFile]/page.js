"use client";
import NavBar from '../components/NavBar';
import { useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';

export default function Page({ params }) {
 const router = useRouter();
 const [isAuthorized, setIsAuthorized] = useState(false);

 // Authorization check
 useEffect(() => {
 (async () => {
 const userLoggedIn = localStorage.getItem('username');
 const resolvedParams = await params;
 if (userLoggedIn === resolvedParams.ParkingFile) {
 setIsAuthorized(true);
 } else {
 router.push('/');
 }
 })();
 }, [params, router]);

 const Navigation = () => {
 router.push('/');
 }

 // JSON structured state
 const [parkingData, setParkingData] = useState({
 "parking_application": {
 "first_name": "",
 "last_name": "",
 "email": "",
 "student_id": "",
 "phone_number": "",
 "Study_Department": "",
 "car_type": "",
 "car_number": "",
 "license_image": null // Will store base64 string
 }
 });

 const handleChange = (e) => {
 const { id, value, type, files } = e.target;

 if (type === 'file') {
 // Handle file input
 const file = files[0];
 if (file) {
 const reader = new FileReader();
 reader.onloadend = () => {
 setParkingData(prev => ({
 parking_application: {
 ...prev.parking_application,
 license_image: reader.result // This will be base64 string
 }
 }));
 };
 reader.readAsDataURL(file);
 }
 } else {
 // Handle other inputs
 setParkingData(prev => ({
 parking_application: {
 ...prev.parking_application,
 [id]: value
 }
 }));
 }
 };

 const handleSignUp = async () => {
    const { parking_application } = parkingData;
   
    // Validation check
    if (!parking_application.first_name ||
        !parking_application.last_name ||
        !parking_application.student_id ||
        !parking_application.email ||
        !parking_application.phone_number ||
        !parking_application.Study_Department ||
        !parking_application.car_type ||
        !parking_application.car_number) {
        alert("Please fill in all fields!");
        return;
    }

    // Check if file is selected and processed
    if (!parking_application.license_image) {
        alert("Please select a license file!");
        return;
    }

    try {
        console.log('Sending data:', JSON.stringify(parkingData));
       
        const response = await fetch('http://localhost:5000/documents', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(parkingData)
        });

        // First, check if the response is JSON
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            const data = await response.json();
            if (response.ok) {
                alert('Application submitted successfully!');
                router.push('/');
            } else {
                alert(`Error: ${data.message}`);
            }
        } else {
            // Handle non-JSON response
            const text = await response.text();
            throw new Error(text);
        }
    } catch (err) {
        console.error('Error details:', err);
        alert('An unexpected error occurred. Please try again later.');
    }
};
 return (
 <div className="flex flex-col items-center justify-center h-screen bg-[#fff] rtl">
 <NavBar children={localStorage.getItem('username')}></NavBar>
 <div className="bg-[#fff] rounded-2xl box-border min-h-[600px] p-5 w-[520px]">
 <div className="text-[#eee] font-sans text-4xl font-semibold mt-8 text-center text-green-500">
 Application Form
 </div>

 <div className="relative w-full mt-4">
 <input
 id="first_name"
 value={parkingData.parking_application.first_name}
 onChange={handleChange}
 className="bg-[#fff] h-[60px] rounded-xl border border-green-500 box-border text-bg-black text-lg outline-none px-5 pt-1 w-full"
 type="text"
 placeholder="First Name"
 />
 </div>

 <div className="relative w-full mt-4">
 <input
 id="last_name"
 value={parkingData.parking_application.last_name}
 onChange={handleChange}
 className="bg-[#fff] h-[60px] rounded-xl border border-green-500 box-border text-bg-black text-lg outline-none px-5 pt-1 w-full"
 type="text"
 placeholder="Last Name"
 />
 </div>

 <div className="relative w-full mt-4">
 <input
 id="student_id"
 value={parkingData.parking_application.student_id}
 onChange={handleChange}
 className="bg-[#fff] h-[60px] rounded-xl border border-green-500 box-border text-bg-black text-lg outline-none px-5 pt-1 w-full"
 type="text"
 placeholder="ID"
 />
 </div>

 <div className="relative w-full mt-4">
 <input
 id="email"
 value={parkingData.parking_application.email}
 onChange={handleChange}
 className="bg-[#fff] h-[60px] rounded-xl border border-green-500 box-border text-bg-black text-lg outline-none px-5 pt-1 w-full"
 type="email"
 placeholder="Email"
 />
 </div>

 <div className="relative w-full mt-4">
 <input
 id="phone_number"
 value={parkingData.parking_application.phone_number}
 onChange={handleChange}
 className="bg-[#fff] h-[60px] rounded-xl border border-green-500 box-border text-bg-black text-lg outline-none px-5 pt-1 w-full"
 type="text"
 placeholder="Phone Number"
 />
 </div>

 <div className="relative w-full mt-4">
 <input
 id="Study_Department"
 value={parkingData.parking_application.Study_Department}
 onChange={handleChange}
 className="bg-[#fff] h-[60px] rounded-xl border border-green-500 box-border text-bg-black text-lg outline-none px-5 pt-1 w-full"
 type="text"
 placeholder="Department"
 />
 </div>

 <div className="relative w-full mt-4">
 <input
 id="car_type"
 value={parkingData.parking_application.car_type}
 onChange={handleChange}
 className="bg-[#fff] h-[60px] rounded-xl border border-green-500 box-border text-bg-black text-lg outline-none px-5 pt-1 w-full"
 type="text"
 placeholder="Car Type"
 />
 </div>

 <div className="relative w-full mt-4">
 <input
 id="car_number"
 value={parkingData.parking_application.car_number}
 onChange={handleChange}
 className="bg-[#fff] h-[60px] rounded-xl border border-green-500 box-border text-bg-black text-lg outline-none px-5 pt-1 w-full"
 type="text"
 placeholder="Car Number"
 />
 </div>

 <div className="relative w-full mt-4">
 <label htmlFor="license_image" className="text-lg">Driver's License:</label>
 <input
 id="license_image"
 onChange={handleChange}
 className="bg-[#fff] h-[60px] rounded-xl border border-green-500 box-border text-bg-black text-lg outline-none px-5 pt-1 w-full"
 type="file"
 accept="image/*"
 />
 </div>

 <button onClick={handleSignUp} className="bg-green-500 rounded-full border-0 text-[#eee] text-lg h-[50px] mt-9 w-full hover:bg-green-600">
 Send
 </button>
 <button onClick={Navigation} className="bg-[#fff] text-green-500 rounded-full border border-green-500 text-lg h-[50px] mt-5 w-full hover:bg-green-500 hover:text-white">
 back
 </button>
 </div>
 </div>
 );
}