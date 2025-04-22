import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import "./CurrentGame.css";

const CurrentGame = () => {
  const { gameCode } = useParams();
  const [players, setPlayers] = useState([]);
  const [gameVersion, setGameVersion] = useState(null);  // To store the fetched game version
  const [characters, setCharacters] = useState([]);  // To store the fetched characters
  const [isGameStarted, setIsGameStarted] = useState(false);  // To control the display of dropdowns and buttons
  const [isFirstNightStarted, setIsFirstNightStarted] = useState(false);  // To control the First Night button visibility
  const [isFirstNightNotSent, setIsFirstNightNotSent] = useState(true)
  const [firstNightPlayers, setFirstNightPlayers] = useState([]);
  const [playerInfo, setPlayerInfo] = useState({});

  const ipAddress = window.location.hostname;
  const apiUrl = `http://${ipAddress}:8000`;

  // Function to fetch players from the backend
  const fetchPlayers = async () => {
    try {
      const response = await fetch(`${apiUrl}/players/game/${gameCode}`);
      const data = await response.json();

      if (data.result === "success") {
        setPlayers(data.players); // Update state with the new player list
      } else {
        console.error("Failed to fetch players:", data.error);
      }
    } catch (error) {
      console.error("Error fetching players:", error);
    }
  };

  // Fetch game version based on gameCode
  const fetchGameVersion = async () => {
    try {
      const response = await fetch(`${apiUrl}/games/${gameCode}`);
      const data = await response.json();

      if (data.result === "success") {
        setGameVersion(data.game.game_version);  // Set the game version from the response
        console.log("Game version fetched:", data.game.game_version);
      } else {
        console.error("Failed to fetch game version:", data.error);
      }
    } catch (error) {
      console.error("Error fetching game version:", error);
    }
  };

  // Fetch characters based on the game version
  const fetchCharacters = async () => {
    if (gameVersion) {
      try {
        console.log("Fetching characters for game version:", gameVersion);
        const response = await fetch(`${apiUrl}/characters/game_version/${gameVersion}`);
        const data = await response.json();

        if (data.result === "success") {
          setCharacters(data.characters);  // Set the characters based on the game version
          console.log("Characters fetched:", data.characters);
        } else {
          console.error("Failed to fetch characters:", data.error);
        }
      } catch (error) {
        console.error("Error fetching characters:", error);
      }
    }
  };

  // Fetch players when component mounts & every 5 seconds
  useEffect(() => {
    fetchPlayers(); // Initial fetch

    // Poll the server every 5 seconds to get new players
    const interval = setInterval(fetchPlayers, 5000);

    return () => clearInterval(interval); // Cleanup on component unmount
  }, [gameCode]);

  // Fetch characters after game version is set
  useEffect(() => {
    if (gameVersion) {
      fetchCharacters(); // Only fetch characters after gameVersion is set
    }
  }, [gameVersion]); // This effect depends on the gameVersion state

  // Handle the "Start Game" button click
  const handleStartGame = async () => {
    await fetchGameVersion(); // Fetch the game version first
    setIsGameStarted(true); // Then enable the dropdowns by setting isGameStarted to true
  };

  const handleStartFirstNight = async () => {
    // Collect player selections and update their character_id
    const updatedPlayers = {
      "players": players.map((player, index) => {
        const selectedCharacter = document.getElementById(`character-dropdown-${index}`).value;
        const character = characters.find((char) => char.character_name === selectedCharacter);
        return { player_id: player.player_id, character_id: character ? character.character_id : null };
      })
    };
  
    try {
      // Step 1: Send the update request for all players
      const updateResponse = await fetch(`${apiUrl}/players/update_multiple`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedPlayers),
      });
  
      const updateData = await updateResponse.json();
      if (updateData.result !== "success") {
        console.error("Failed to update players:", updateData.error);
        return;
      }
  
      // Step 2: Fetch first-night players
      const firstNightResponse = await fetch(`${apiUrl}/game/first_night_players`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ game_code: gameCode, game_version: gameVersion }),
      });
      
      const firstNightData = await firstNightResponse.json();

      // Step 2: Update game turn and time_of_day
      const firstNightGameUpdate = await fetch(`${apiUrl}/games/${gameCode}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ turn: 1, time_of_day: "night" }),
      });

      const firstNightGameUpdateData = await firstNightGameUpdate.json();

      if (firstNightData.result === "success" && firstNightGameUpdateData.result === "success") {
        setFirstNightPlayers(firstNightData.players);
        setIsFirstNightStarted(true); // Mark first night as started
        const initialPlayerInfo = {};
        firstNightData.players.forEach(player => {
          initialPlayerInfo[player.player_id] = {
            information_received: player.character_action_info.information_recieved || ""
          };
        });
        setPlayerInfo(initialPlayerInfo);
      } else {
        console.error("Failed to get first-night players:", firstNightData.message);
      }
    } catch (error) {
      console.error("Error during first night setup:", error);
    }
  };

  const handleInputChange = (playerId, value) => {
    setPlayerInfo(prev => ({
      ...prev,
      [playerId]: { ...prev[playerId], information_received: value }
    }));
  };

  const handleSend = async () => {
    const updatedData = firstNightPlayers.map(player => ({
      player_id: player.player_id,
      character_id: player.character_id,
      designation: player.designation,
      first_night_order: player.first_night_order,
      receives_information: player.character_action_info.recieve_information,
      information_received: playerInfo[player.player_id]?.information_received || "",
      action: player.character_action_info.action,
      response_required: player.character_action_info.response_required
    }));

    try {
      const response = await fetch(`${apiUrl}/game/update_first_night_info`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ game_code: gameCode, players: updatedData }),
      });

      const responseData = await response.json();
      if (responseData.result === "success") {
        console.log("First night info successfully sent.");
        setIsFirstNightNotSent(false);
      } else {
        console.error("Failed to send first-night info:", responseData.error);
      }
    } catch (error) {
      console.error("Error sending first-night info:", error);
    }
  };

  const handleEndNight = async () => {
    // Here you can implement what happens when "Send" is clicked (e.g., sending actions, updating game state, etc.)
    console.log("Sending data for first night...");
    // Further actions like sending the night actions can go here
  };

  return (
    <div className="current-game-container">
      <h1 className="game-title">Current Game</h1>
      <div className="game-code">
        <label>Game Code:</label>
        <div className="code-box">{gameCode}</div>
      </div>

      <hr className="divider-line" />

      <h2 className="player-title">Players</h2>
      <ul className="player-list">
        {players.map((player, index) => (
          <li key={index} className="player-item">
            {player.player_name}
            {isGameStarted && !isFirstNightStarted && (
              <select id={`character-dropdown-${index}`} className="character-dropdown">
                {characters.map((character, idx) => (
                  <option key={idx} value={character.character_name}>
                    {character.character_name}
                  </option>
                ))}
              </select>
            )}
          </li>
        ))}
      </ul>

      <div className="button-container">
        {!isGameStarted && <button className="game-button" onClick={handleStartGame}>Start Game</button>}
        {isGameStarted && !isFirstNightStarted && <button className="game-button" onClick={handleStartFirstNight}>Start First Night</button>}
      </div>

      {isFirstNightStarted && isFirstNightNotSent && (
        <div className="first-night-actions">
          <h2>First Night Actions</h2>
          <ul>
            {firstNightPlayers.map((player, index) => (
              <li key={index} className="first-night-player">
                <strong>{player.player_name}</strong> - <em>{player.character_name}</em>
                <p><strong>Designation:</strong> {player.designation}</p>
                <p><strong>First Night Order:</strong> {player.first_night_order}</p>
                <p><strong>Receives Information:</strong> {player.character_action_info.recieve_information ? "Yes" : "No"}</p>
                {player.character_action_info.recieve_information && (
                  <div>
                    <label>Information Received:</label>
                    <textarea className='info-textarea' value={playerInfo[player.player_id]?.information_received || ""} onChange={(e) => handleInputChange(player.player_id, e.target.value)} />
                  </div>
                )}
                <p><strong>Action:</strong> {player.character_action_info.action}</p>
                <p><strong>Response Required:</strong> {player.character_action_info.response_required ? "Yes" : "No"}</p>
              </li>
            ))}
          </ul>
        </div>
      )}
      {isFirstNightStarted && isFirstNightNotSent && (
        <div className="send-container">
          <button className="game-button" onClick={handleSend}>Send</button>
        </div>
      )}
      {!isFirstNightNotSent && <h4>First Night Info Sent</h4>}
      {isFirstNightStarted && (
        <div className="send-container">
          <button className="game-button2" onClick={handleEndNight}>End Night</button>
        </div>
      )}
    </div>
  );
};

export default CurrentGame;





