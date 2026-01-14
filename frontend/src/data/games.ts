// 25 款熱門遊戲（不同解像度的 VRAM 需求，單位：GB）
export interface GameRequirements {
  name: string
  // 不同解像度的 VRAM 需求
  vramByResolution: {
    '1280x720': number   // 720p
    '1920x1080': number  // 1080p
    '2560x1440': number  // 1440p
    '3840x2160': number  // 4K
  }
  ram: number  // RAM 需求通常不隨解像度變化
}

export const POPULAR_GAMES: GameRequirements[] = [
  { name: "Minecraft", vramByResolution: { '1280x720': 4, '1920x1080': 6, '2560x1440': 8, '3840x2160': 10 }, ram: 16 },
  { name: "Elden Ring", vramByResolution: { '1280x720': 4, '1920x1080': 6, '2560x1440': 8, '3840x2160': 10 }, ram: 16 },
  { name: "Alan Wake 2", vramByResolution: { '1280x720': 6, '1920x1080': 8, '2560x1440': 10, '3840x2160': 12 }, ram: 16 },
  { name: "Fortnite", vramByResolution: { '1280x720': 3, '1920x1080': 4, '2560x1440': 6, '3840x2160': 8 }, ram: 8 },
  { name: "Escape from Tarkov", vramByResolution: { '1280x720': 3, '1920x1080': 4, '2560x1440': 6, '3840x2160': 8 }, ram: 16 },
  { name: "Dragon's Dogma 2", vramByResolution: { '1280x720': 6, '1920x1080': 8, '2560x1440': 10, '3840x2160': 12 }, ram: 16 },
  { name: "Cyberpunk 2077", vramByResolution: { '1280x720': 6, '1920x1080': 8, '2560x1440': 10, '3840x2160': 12 }, ram: 16 },
  { name: "Counter-Strike 2", vramByResolution: { '1280x720': 3, '1920x1080': 4, '2560x1440': 6, '3840x2160': 8 }, ram: 8 },
  { name: "Valorant", vramByResolution: { '1280x720': 3, '1920x1080': 4, '2560x1440': 6, '3840x2160': 8 }, ram: 8 },
  { name: "Overwatch 2", vramByResolution: { '1280x720': 3, '1920x1080': 4, '2560x1440': 6, '3840x2160': 8 }, ram: 8 },
  { name: "Apex Legends", vramByResolution: { '1280x720': 3, '1920x1080': 4, '2560x1440': 6, '3840x2160': 8 }, ram: 8 },
  { name: "Halo Infinite", vramByResolution: { '1280x720': 4, '1920x1080': 6, '2560x1440': 8, '3840x2160': 10 }, ram: 16 },
  { name: "Ready or Not", vramByResolution: { '1280x720': 4, '1920x1080': 6, '2560x1440': 8, '3840x2160': 10 }, ram: 16 },
  { name: "PUBG: Battlegrounds", vramByResolution: { '1280x720': 3, '1920x1080': 4, '2560x1440': 6, '3840x2160': 8 }, ram: 8 },
  { name: "Rust", vramByResolution: { '1280x720': 4, '1920x1080': 6, '2560x1440': 8, '3840x2160': 10 }, ram: 16 },
  { name: "Assetto Corsa Competizione", vramByResolution: { '1280x720': 4, '1920x1080': 6, '2560x1440': 8, '3840x2160': 10 }, ram: 16 },
  { name: "iRacing", vramByResolution: { '1280x720': 4, '1920x1080': 6, '2560x1440': 8, '3840x2160': 10 }, ram: 16 },
  { name: "Cities: Skylines", vramByResolution: { '1280x720': 3, '1920x1080': 4, '2560x1440': 6, '3840x2160': 8 }, ram: 16 },
  { name: "Starfield", vramByResolution: { '1280x720': 6, '1920x1080': 8, '2560x1440': 10, '3840x2160': 12 }, ram: 16 },
  { name: "Forza Horizon 5", vramByResolution: { '1280x720': 4, '1920x1080': 6, '2560x1440': 8, '3840x2160': 10 }, ram: 16 },
  { name: "Red Dead Redemption 2", vramByResolution: { '1280x720': 4, '1920x1080': 6, '2560x1440': 8, '3840x2160': 10 }, ram: 16 },
  { name: "The Witcher 3", vramByResolution: { '1280x720': 4, '1920x1080': 6, '2560x1440': 8, '3840x2160': 10 }, ram: 16 },
  { name: "Baldur's Gate 3", vramByResolution: { '1280x720': 4, '1920x1080': 6, '2560x1440': 8, '3840x2160': 10 }, ram: 16 },
  { name: "Hogwarts Legacy", vramByResolution: { '1280x720': 6, '1920x1080': 8, '2560x1440': 10, '3840x2160': 12 }, ram: 16 },
  { name: "Grand Theft Auto V", vramByResolution: { '1280x720': 3, '1920x1080': 4, '2560x1440': 6, '3840x2160': 8 }, ram: 8 }
]



