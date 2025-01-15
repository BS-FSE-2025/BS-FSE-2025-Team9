"use client"

import React, { useState } from "react";
import anime from "animejs";
import NavBar from "../../components/NavBar";

const LotteryPage = () => {
  const [result, setResult] = useState([]);
  const [winners, setWinners] = useState([]);  // Store winners as an array of objects
  const [loading, setLoading] = useState(false);
  const [numWinners, setNumWinners] = useState(1);
  const [crystalActive, setCrystalActive] = useState(false);

  // Handle the lottery draw
  const handleLotteryClick = async () => {
    setLoading(true);
    setResult([]);  // Reset result
    setCrystalActive(true);

    try {
      const response = await fetch("https://bs-fse-2025-team9.onrender.com/documents");

      if (!response.ok) {
        throw new Error("Error fetching documents");
      }

      const documents = await response.json();

      if (documents.length === 0) {
        setResult([{ message: "No documents found." }]);
        setLoading(false);
        return;
      }

      if (numWinners > documents.length) {
        setResult([{ message: "Number of winners exceeds the total number of documents." }]);
        setLoading(false);
        return;
      }

      let winners = [];
      let selectedIndexes = new Set();

      while (winners.length < numWinners) {
        const randomIndex = Math.floor(Math.random() * documents.length);
        if (!selectedIndexes.has(randomIndex)) {
          selectedIndexes.add(randomIndex);
          winners.push(documents[randomIndex]);
        }
      }

      // Save winners as an array of objects
      setWinners(winners);  // Now 'winners' is an array of winner objects

      // Display winner details
      const winnerDetails = winners.map((winner) => ({
        student_id: winner.student_id,
        first_name: winner.first_name,
        last_name: winner.last_name,
      }));

      setTimeout(() => {
        setResult(winnerDetails);  // Set result as winner details (array of objects)
        setCrystalActive(false);
        setLoading(false);
      }, 3000);
    } catch (error) {
      setResult([{ message: "An error occurred. Please try again." }]);
      console.error("Error fetching documents:", error.message);
      setCrystalActive(false);
      setLoading(false);
    }
  };

  // Send results to the server
  const handleSendResults = async () => {
    // Map over the winners array and get their student IDs
    const winnerIds = winners.map((winner) => winner.student_id);

    try {
      const response = await fetch("https://bs-fse-2025-team9.onrender.com/documents/update-winners", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ winners: winnerIds }), // Send an array of student_ids
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Winners updated successfully12!`);
      } else {
        const errorData = await response.json();
        alert(`Error: ${errorData.message}`);
      }
    } catch (error) {
      console.error("Error updating winners:", error);
      alert("An unexpected error occurred. Please try again later.");
    }
  };

  // Animation for the crystal ball
  React.useEffect(() => {
    if (crystalActive) {
      anime({
        targets: ".crystal-ball",
        scale: [1, 1.2, 1],
        opacity: [0.5, 1],
        duration: 1000,
        easing: "easeInOutSine",
        loop: true,
      });
    } else {
      anime.remove(".crystal-ball");
    }
  }, [crystalActive]);

  return (
    <div>
      <NavBar userRole={localStorage.getItem("userRole")}>
        {localStorage.getItem("studentId")}
      </NavBar>
      <div className="min-h-screen bg-gradient-to-br from-green-300 via-teal-200 to-cyan-300 flex items-center justify-center p-4 sm:p-8">
        <div className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-md space-y-6">
          <h1 className="text-center text-2xl sm:text-4xl font-serif font-light tracking-wide text-gray-800 uppercase">
            Lottery
          </h1>
          <div className="text-center text-sm font-medium text-gray-600 uppercase">
            Enter Number Of Winners
          </div>
          <input
            type="number"
            min="1"
            value={numWinners}
            onChange={(e) => setNumWinners(Number(e.target.value))}
            className="block mx-auto w-20 p-2 border border-gray-300 rounded text-center text-lg focus:ring-2 focus:ring-green-400 focus:outline-none"
          />
          <button
            onClick={handleLotteryClick}
            disabled={loading}
            className={`mt-7 w-full py-3 bg-gradient-to-r from-green-400 to-cyan-500 text-white font-bold rounded-xl hover:from-cyan-500 hover:to-green-400 shadow-lg transform hover:scale-105 transition-all duration-300`}
          >
            {loading ? "Drawing..." : "Start Lottery"}
          </button>
          {crystalActive && (
            <div className="crystal-ball w-36 h-36 mx-auto rounded-full bg-gradient-to-r from-blue-500 to-pink-500 shadow-lg animate-pulse"></div>
          )}
          {result.length > 0 && (
            <div className="mt-4 text-center">
              <h2 className="text-xl font-semibold mb-2">The Winners Are:</h2>
              <div className="flex justify-center">
                <ul className="list-disc list-inside text-left">
                  {result.map((winner, index) => (
                    <li key={index} className="text-gray-700">
                      {`Name: ${winner.first_name} ${winner.last_name}, ID: ${winner.student_id}`}
                    </li>
                  ))}
                </ul>
              </div>
              {/* Button appears after winners are displayed */}
              <button
                className="mt-6 w-full py-3 bg-gradient-to-r from-red-400 to-orange-500 text-white font-bold rounded-xl hover:from-orange-500 hover:to-red-400 shadow-lg transform hover:scale-105 transition-all duration-300"
                onClick={handleSendResults}
              >
                SEND RESULTS TO STUDENTS
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LotteryPage;
