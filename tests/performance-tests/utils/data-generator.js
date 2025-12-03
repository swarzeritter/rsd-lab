import { randomString, randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

export function generateTravelPlan() {
  const titles = [
    'Summer Vacation in Europe',
    'Winter Ski Trip',
    'Beach Holiday',
    'City Break',
    'Adventure Travel',
    'Cultural Tour',
    'Road Trip',
    'Mountain Hiking',
  ];
  
  const descriptions = [
    'An amazing journey through beautiful places',
    'Exploring new cultures and traditions',
    'Relaxing and enjoying nature',
    'Discovering hidden gems',
    'Creating unforgettable memories',
  ];
  
  const currencies = ['USD', 'EUR', 'UAH', 'GBP'];
  
  const startDate = new Date();
  startDate.setDate(startDate.getDate() + randomIntBetween(1, 30));
  
  const endDate = new Date(startDate);
  endDate.setDate(endDate.getDate() + randomIntBetween(3, 14));
  
  return {
    title: titles[randomIntBetween(0, titles.length - 1)] + ' ' + randomString(5),
    description: descriptions[randomIntBetween(0, descriptions.length - 1)],
    start_date: startDate.toISOString().split('T')[0],
    end_date: endDate.toISOString().split('T')[0],
    budget: randomIntBetween(500, 10000),
    currency: currencies[randomIntBetween(0, currencies.length - 1)],
    is_public: Math.random() > 0.5,
  };
}

export function generateLocation(travelPlanId) {
  const names = [
    'Paris',
    'London',
    'Rome',
    'Barcelona',
    'Amsterdam',
    'Berlin',
    'Prague',
    'Vienna',
    'Budapest',
    'Krakow',
  ];
  
  const addresses = [
    '123 Main Street',
    '456 Central Avenue',
    '789 Park Boulevard',
    '321 Ocean Drive',
    '654 Mountain View',
  ];
  
  const arrivalDate = new Date();
  arrivalDate.setDate(arrivalDate.getDate() + randomIntBetween(1, 30));
  
  const departureDate = new Date(arrivalDate);
  departureDate.setDate(departureDate.getDate() + randomIntBetween(1, 5));
  
  return {
    travel_plan_id: travelPlanId,
    name: names[randomIntBetween(0, names.length - 1)] + ' ' + randomString(3),
    address: addresses[randomIntBetween(0, addresses.length - 1)],
    latitude: (Math.random() * 180 - 90).toFixed(6),
    longitude: (Math.random() * 360 - 180).toFixed(6),
    visit_order: randomIntBetween(1, 10),
    arrival_date: arrivalDate.toISOString(),
    departure_date: departureDate.toISOString(),
    budget: randomIntBetween(100, 2000),
    notes: 'Test location notes ' + randomString(10),
  };
}

