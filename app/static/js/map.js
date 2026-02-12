function initMap() {
  // 1. 地図のデザイン設定（色味を優しく、不要な情報を消す）
  const map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: MID.lat, lng: MID.lng },
    zoom: 14
    , // 少しズームして見やすく
    styles: [
      { "featureType": "water", "elementType": "geometry", "stylers": [{ "color": "#a2daf2" }] },
      { "featureType": "landscape", "stylers": [{ "color": "#f5f5f3" }] },
      { "featureType": "poi.park", "elementType": "geometry", "stylers": [{ "color": "#c8e6c9" }] },
      { "featureType": "road", "elementType": "geometry", "stylers": [{ "color": "#ffffff" }] },
      { "featureType": "poi.business", "stylers": [{ "visibility": "off" }] }, // 他のお店情報を消してスッキリ
      { "stylers": [{ "saturation": -20 }, { "lightness": 10 }] }
    ],
    disableDefaultUI: true,
    zoomControl: true,
  });

  // 2. 中間地点：目立つ「フラッグ」のアイコン（駅のピンは表示しません）
  new google.maps.Marker({
    map,
    position: { lat: MID.lat, lng: MID.lng },
    label: {
      text: "M",
      color: "#ffffff",
      fontWeight: "bold"
    },
    title: "ここが真ん中！",
    icon: {
      url: 'https://cdn-icons-png.flaticon.com/512/8059/8059101.png',
      scaledSize: new google.maps.Size(50, 50),
      labelOrigin: new google.maps.Point(25, 15)
    },
    zIndex: 100 // 重なった時に一番上にくるように
  });

  // 3. 周辺のお店：可愛い「お花」のアイコン
  SHOPS.forEach((s, index) => {
    const marker = new google.maps.Marker({
      map,
      position: { lat: s.lat, lng: s.lng },
      title: s.name,
      label: {
        text: String(index + 1), // リストの番号を表示して分かりやすく
        color: "#5d4037",
        fontSize: "12px",
        fontWeight: "bold"
      },
      icon: {
        url: 'https://cdn-icons-png.flaticon.com/512/346/346167.png',
        scaledSize: new google.maps.Size(35, 35),
        labelOrigin: new google.maps.Point(17, 45) // 番号をお花の下に表示
      }
    });

    // お店をクリックした時の吹き出し
    const infoWindow = new google.maps.InfoWindow({
        content: `
          <div style="padding:5px; font-family:'Kiwi Maru', serif; color:#5d4037;">
            <strong>${s.name}</strong><br>
            <span style="font-size:11px;">${s.budget}</span>
          </div>`
    });
    marker.addListener("click", () => {
        infoWindow.open(map, marker);
    });
  });
}

window.initMap = initMap;