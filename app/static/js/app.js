document.addEventListener('DOMContentLoaded', function() {

    const API_ENDPOINT = 'https://your-backend-service.com';
    const DEMO_MODE = true;
    const searchForm = document.getElementById('search-form');
    const locationInput = document.getElementById('location');
    const petTypeOptions = document.querySelectorAll('.pet-type-option');
    const priceSelect = document.getElementById('price');
    const distanceSelect = document.getElementById('distance');
    const serviceTypesContainer = document.getElementById('service-types');
    const resultsContainer = document.getElementById('results-container');
    const resultsList = document.getElementById('results-list');
    const loadingIndicator = document.getElementById('loading');
    const noResultsMessage = document.getElementById('no-results');
    const apiStatus = document.getElementById('api-status');
    const appliedFiltersCard = document.getElementById('applied-filters');
    const filterChips = document.getElementById('filter-chips');
    const clearFiltersBtn = document.getElementById('clear-filters');

    const landingView = document.getElementById('landing-view');
    const searchView = document.getElementById('search-view');
    const startSearchBtn = document.getElementById('start-search-btn');
    const backToHomeBtn = document.getElementById('back-to-home-btn');

    if (startSearchBtn) {
        startSearchBtn.addEventListener('click', function() {
            if (landingView) {
                landingView.style.display = 'none';
            }

            if (searchView) {
                searchView.style.display = 'block';
            }

            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    if (backToHomeBtn) {
        backToHomeBtn.addEventListener('click', function() {
            if (searchView) {
                searchView.style.display = 'none';
            }

            if (landingView) {
                landingView.style.display = 'flex';

                const petIcons = landingView.querySelectorAll('.pet-icon');
                petIcons.forEach(icon => {
                    icon.style.display = 'block';
                });
            }

            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    let selectedPetType = 'dog';
    let selectedSpecialties = [];

    const specialtyOptions = [
        { id: 'general', name: 'General Practice', category: 'services' },
        { id: 'emergency', name: 'Emergency Care', category: 'services' },
        { id: 'surgery', name: 'Surgery', category: 'services' },
        { id: 'dental', name: 'Dental', category: 'services' },
        { id: 'dermatology', name: 'Dermatology', category: 'services' },
        { id: 'exotic', name: 'Exotic Animals', category: 'pet_type' },
        { id: 'birds', name: 'Birds', category: 'pet_type' },
        { id: 'reptiles', name: 'Reptiles', category: 'pet_type' },
        { id: 'small_mammals', name: 'Small Mammals', category: 'pet_type' }
    ];

    function initializeFilters() {
        specialtyOptions.forEach(specialty => {
            const checkbox = createFilterCheckbox(specialty.id, specialty.name, 'specialty');
            if (serviceTypesContainer) {
                serviceTypesContainer.appendChild(checkbox);
            }
        });

        document.querySelectorAll('.filter-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', handleFilterChange);
        });
    }

    function createFilterCheckbox(id, name, type) {
        const div = document.createElement('div');
        div.className = 'filter-checkbox-item';

        const input = document.createElement('input');
        input.type = 'checkbox';
        input.className = 'filter-checkbox';
        input.id = `${type}-${id}`;
        input.setAttribute('data-type', type);
        input.setAttribute('data-id', id);

        const label = document.createElement('label');
        label.htmlFor = `${type}-${id}`;
        label.textContent = name;

        div.appendChild(input);
        div.appendChild(label);

        return div;
    }

    function handleFilterChange(e) {
        const checkbox = e.target;
        const type = checkbox.getAttribute('data-type');
        const id = checkbox.getAttribute('data-id');

        if (type === 'specialty') {
            if (checkbox.checked) {
                selectedSpecialties.push(id);
            } else {
                selectedSpecialties = selectedSpecialties.filter(item => item !== id);
            }
        }

        updateFilterChips();
    }

    function updateFilterChips() {
        if (!filterChips) return;

        filterChips.innerHTML = '';

        const petTypeChip = createFilterChip('Pet Type', getPetTypeName(selectedPetType), 'pet_type');
        filterChips.appendChild(petTypeChip);

        selectedSpecialties.forEach(specialtyId => {
            const specialty = specialtyOptions.find(s => s.id === specialtyId);
            if (specialty) {
                const chip = createFilterChip('Specialty', specialty.name, 'specialty', specialtyId);
                filterChips.appendChild(chip);
            }
        });

        if (priceSelect && priceSelect.value) {
            const priceChip = createFilterChip('Price', priceSelect.value, 'price');
            filterChips.appendChild(priceChip);
        }

        if (distanceSelect) {
            const distanceChip = createFilterChip('Distance', `${distanceSelect.value} miles`, 'distance');
            filterChips.appendChild(distanceChip);
        }

        if (appliedFiltersCard) {
            if (selectedSpecialties.length > 0 || (priceSelect && priceSelect.value)) {
                appliedFiltersCard.classList.remove('d-none');
            } else {
                appliedFiltersCard.classList.add('d-none');
            }
        }
    }

    function createFilterChip(type, value, filterType, filterId) {
        const chip = document.createElement('span');
        chip.className = `badge me-2 mb-2 p-2`;

        const typeSpan = document.createElement('span');
        typeSpan.className = 'text-secondary me-1';
        typeSpan.textContent = `${type}:`;

        const valueSpan = document.createElement('span');
        valueSpan.className = 'fw-bold';
        valueSpan.textContent = value;

        chip.appendChild(typeSpan);
        chip.appendChild(valueSpan);

        if (filterType !== 'pet_type' && filterType !== 'distance') {
            const removeBtn = document.createElement('button');
            removeBtn.className = 'btn-close btn-close-sm ms-2';
            removeBtn.style.fontSize = '0.6rem';
            removeBtn.setAttribute('aria-label', 'Remove filter');
            removeBtn.setAttribute('data-filter-type', filterType);
            if (filterId) {
                removeBtn.setAttribute('data-filter-id', filterId);
            }

            removeBtn.addEventListener('click', function() {
                removeFilter(filterType, filterId);
            });

            chip.appendChild(removeBtn);
        }

        return chip;
    }

    function removeFilter(filterType, filterId) {
        if (filterType === 'specialty' && filterId) {
            selectedSpecialties = selectedSpecialties.filter(id => id !== filterId);
            const checkbox = document.getElementById(`specialty-${filterId}`);
            if (checkbox) checkbox.checked = false;
        } else if (filterType === 'price' && priceSelect) {
            priceSelect.value = '';
        }

        updateFilterChips();
        submitSearch();
    }

    function clearAllFilters() {
        document.querySelectorAll('.filter-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });

        selectedSpecialties = [];

        if (priceSelect) priceSelect.value = '';

        updateFilterChips();
        submitSearch();
    }

    function getPetTypeName(petType) {
        switch (petType) {
            case 'dog': return 'Dog';
            case 'cat': return 'Cat';
            case 'bird': return 'Bird';
            case 'exotic': return 'Exotic';
            default: return 'Any';
        }
    }

    petTypeOptions.forEach(option => {
        option.addEventListener('click', function() {
            petTypeOptions.forEach(opt => opt.classList.remove('active'));
            this.classList.add('active');
            selectedPetType = this.getAttribute('data-pet-type');
            updateFilterChips();
        });
    });

    initializeFilters();
    
    function checkApiStatus() {
        if (!apiStatus) return;
        
        if (DEMO_MODE) {
            apiStatus.textContent = 'Demo Mode';
            apiStatus.classList.remove('bg-secondary', 'bg-danger');
            apiStatus.classList.add('bg-warning');
            return;
        }
        
        fetch(`${API_ENDPOINT}/api/data-sources`)
            .then(response => response.json())
            .then(data => {
                const sources = data.enabled_sources || [];
                if (sources.length > 0) {
                    apiStatus.textContent = `${sources.length} Data Source${sources.length > 1 ? 's' : ''} Active`;
                    apiStatus.classList.remove('bg-secondary', 'bg-danger');
                    apiStatus.classList.add('bg-success');
                } else {
                    apiStatus.textContent = 'No Data Sources Available';
                    apiStatus.classList.remove('bg-secondary', 'bg-success');
                    apiStatus.classList.add('bg-danger');
                }
            })
            .catch(error => {
                console.error('Error checking API status:', error);
                apiStatus.textContent = 'API Status: Error';
                apiStatus.classList.remove('bg-secondary', 'bg-success');
                apiStatus.classList.add('bg-danger');
            });
    }
    
    checkApiStatus();

    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', clearAllFilters);
    }

    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitSearch();
        });
    }

    function submitSearch() {
        if (!locationInput || !loadingIndicator || !resultsContainer) return;

        const location = locationInput.value.trim();
        if (!location) {
            showAlert('Please enter a location.', 'danger');
            return;
        }

        loadingIndicator.classList.remove('d-none');
        resetResults();
        updateFilterChips();

        const timestamp = new Date().getTime();
        const searchData = {
            location: location,
            pet_type: selectedPetType,
            price: priceSelect ? priceSelect.value : '',
            max_distance: distanceSelect ? parseFloat(distanceSelect.value) : 10,
            specialties: selectedSpecialties,
            cache_buster: timestamp
        };

        if (DEMO_MODE) {
            setTimeout(() => {
                loadingIndicator.classList.add('d-none');
                displayResults(getMockResults(location, selectedPetType));
            }, 1500);
            return;
        }

        getUserCoordinates()
            .then(coordinates => {
                if (coordinates) {
                    searchData.latitude = coordinates.latitude;
                    searchData.longitude = coordinates.longitude;
                }

                return fetch(`${API_ENDPOINT}/api/search`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Cache-Control': 'no-cache'
                    },
                    body: JSON.stringify(searchData)
                });
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Search request failed with status: ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                console.log('Search response received:', data);
                loadingIndicator.classList.add('d-none');
                displayResults(data);
            })
            .catch(error => {
                console.error('Error during search:', error);
                loadingIndicator.classList.add('d-none');
                showAlert('Error searching for veterinarians: ' + error.message, 'danger');
            });
    }

    function getUserCoordinates() {
        return new Promise((resolve) => {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        resolve({
                            latitude: position.coords.latitude,
                            longitude: position.coords.longitude
                        });
                    },
                    () => {
                        resolve(null);
                    },
                    { timeout: 5000 }
                );
            } else {
                resolve(null);
            }
        });
    }

    function displayResults(data) {
        if (!resultsList || !noResultsMessage || !resultsContainer) return;

        resultsList.innerHTML = '';

        const initialMessage = document.querySelector('.alert-info');
        if (initialMessage) initialMessage.style.display = 'none';

        console.log("Displaying results:", data);  

        if (data.recommendations && data.recommendations.length > 0) {
            resultsList.classList.remove('d-none');
            noResultsMessage.classList.add('d-none');

            data.recommendations.forEach(vet => {
                const vetCard = createVetCard(vet);
                resultsList.appendChild(vetCard);
            });

            showAlert(`Found ${data.count} veterinarians matching your criteria.`, 'success');
        } else {
            resultsList.classList.add('d-none');
            noResultsMessage.classList.remove('d-none');

            if (data.data_sources && data.data_sources.length > 0) {
                const sourceList = data.data_sources.join(', ');
                showAlert(`No results found. We checked: ${sourceList}`, 'info');
            } else {
                showAlert('No veterinarians found matching your criteria. Try adjusting your search.', 'info');
            }
        }

        resultsContainer.scrollIntoView({ behavior: 'smooth' });
    }

    function resetResults() {
        if (!resultsList || !noResultsMessage) return;

        resultsList.innerHTML = '';
        noResultsMessage.classList.add('d-none');

        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            if (!alert.classList.contains('alert-info') || alert.style.display === 'none') {
                alert.remove();
            }
        });
    }

    function createVetCard(vet) {
        const card = document.createElement('div');
        card.className = 'card mb-3 vet-card';

        let categories = '';
        if (Array.isArray(vet.categories)) {
            categories = vet.categories.map(cat => {
                return typeof cat === 'object' ? cat.title : cat;
            }).join(', ');
        }

        let petEmojis = '🐕 🐈';
        if (vet.handles_exotic) {
            petEmojis += ' 🦜 🦎';
        }

        const address = vet.address || 
                        (vet.location && Array.isArray(vet.location.display_address) 
                        ? vet.location.display_address.join(', ') 
                        : 'Address not available');

        const price = vet.price || '$$';
        const rating = vet.rating ? parseFloat(vet.rating).toFixed(1) + '★' : 'Not Rated';

        card.innerHTML = `
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0">${vet.name}</h5>
                <div>
                    <span class="badge bg-primary">${price}</span>
                    <span class="badge bg-warning text-dark">${rating}</span>
                </div>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-8">
                        <p><strong>Address:</strong> ${address}</p>
                        <p><strong>Phone:</strong> ${vet.phone || 'Not available'}</p>
                        <p><strong>Pet Types:</strong> ${petEmojis}</p>
                        <p><strong>Services:</strong> ${categories || 'General veterinary services'}</p>

                        ${vet.distance ? `<p><strong>Distance:</strong> ${typeof vet.distance === 'number' ? vet.distance.toFixed(1) : vet.distance} miles away</p>` : ''}

                        ${vet.recommendation_reasons && vet.recommendation_reasons.length > 0 ? 
                            `<div class="mt-3 recommendation-reasons">
                                <h6>Why We Recommend:</h6>
                                <ul class="reasons-list">
                                    ${vet.recommendation_reasons.map(reason => {
                                        if (!reason.toLowerCase().includes('miles from')) {
                                            return `<li>${reason}</li>`;
                                        }
                                        return '';
                                    }).join('')}
                                </ul>
                            </div>` : ''
                        }
                    </div>
                    <div class="col-md-4">
                        ${vet.image_url ? 
                            `<div class="vet-image" style="background-image: url('${vet.image_url}');"></div>` : 
                            `<div class="no-image d-flex align-items-center justify-content-center">
                                <span style="font-size: 3rem;">🏥</span>
                            </div>`
                        }
                    </div>
                </div>

                ${vet.reviews && vet.reviews.length > 0 ? 
                    `<div class="mt-3">
                        <h6>Recent Review:</h6>
                        <div class="review-quote">
                            "${vet.reviews[0].text ? (vet.reviews[0].text.substring(0, 150) + (vet.reviews[0].text.length > 150 ? '...' : '')) : 'No review text available'}"
                        </div>
                    </div>` : ''
                }

                ${vet.url ? `<a href="${vet.url}" target="_blank" class="btn btn-sm btn-outline-primary mt-3">Visit Website</a>` : ''}

                ${vet.sources ? 
                    `<div class="mt-2 small text-muted">Data source: ${Array.isArray(vet.sources) ? vet.sources.join(', ') : (typeof vet.sources === 'string' ? vet.sources : 'Multiple sources')}</div>` : 
                    (vet.source ? `<div class="mt-2 small text-muted">Data source: ${vet.source}</div>` : '')
                }
            </div>
        `;

        return card;
    }

    function showAlert(message, type) {
        if (!resultsContainer) return;

        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.role = 'alert';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        const existingAlerts = resultsContainer.querySelectorAll(`.alert-${type}`);
        existingAlerts.forEach(alert => {
            alert.remove();
        });

        resultsContainer.prepend(alertDiv);

        if (type !== 'danger') {
            setTimeout(() => {
                alertDiv.classList.remove('show');
                setTimeout(() => alertDiv.remove(), 300);
            }, 5000);
        }
    }

    // Mock data for demo mode
    function getMockResults(location, petType) {
        const cityName = location.split(',')[0].trim();
        const count = Math.floor(Math.random() * 5) + 3; // 3-7 results
        const recommendations = [];
        
        const vetNames = [
            "City Animal Hospital",
            "Main Street Veterinary Clinic",
            "Happy Paws Pet Care",
            "Healing Hands Vet Center",
            "Lakeside Animal Clinic",
            "Oakwood Veterinary Hospital",
            "Riverside Pet Health",
            "Sunset Boulevard Animal Care",
            "Downtown Pet Hospital",
            "Green Valley Veterinary"
        ];
        
        const specialties = [
            "General Veterinary Services",
            "Emergency Care",
            "Surgery",
            "Dental Care",
            "Dermatology",
            "Orthopedics",
            "Cardiology",
            "Neurology"
        ];
        
        const reviewTexts = [
            "The staff was incredibly caring and professional. Our {pet} received excellent treatment.",
            "Dr. Smith took great care of our {pet} during a recent emergency. Highly recommend!",
            "We've been bringing our {pet} here for years. Always a positive experience.",
            "The clinic is clean, the staff is friendly, and the care is top-notch.",
            "They really took the time to explain my {pet}'s condition and treatment options.",
            "Reasonable prices and excellent care. Our {pet} is doing much better now!",
            "The vets here are knowledgeable and patient. They made our nervous {pet} feel at ease.",
            "State-of-the-art facility with compassionate staff. Wouldn't take our {pet} anywhere else."
        ];
        
        const reasons = [
            "Highly rated by local pet owners",
            "Specialized care for your pet's needs",
            "Extended hours for busy pet parents",
            "Compassionate and experienced staff",
            "Affordable pricing options",
            "Modern treatment facilities",
            "Positive patient reviews"
        ];
        
        for (let i = 0; i < count; i++) {
            const name = vetNames[i % vetNames.length] + (i >= vetNames.length ? " " + Math.ceil(i/vetNames.length) : "");
            const rating = (3.5 + Math.random() * 1.5).toFixed(1);
            const reviewCount = Math.floor(Math.random() * 200) + 20;
            const distance = (Math.random() * 8 + 0.5).toFixed(1);
            const priceTier = Math.ceil(Math.random() * 3);
            const price = "$".repeat(priceTier);
            
            const vet_specialties = [];
            const numSpecialties = Math.floor(Math.random() * 3) + 1;
            for (let j = 0; j < numSpecialties; j++) {
                vet_specialties.push(specialties[Math.floor(Math.random() * specialties.length)]);
            }

            const uniqueSpecialties = [...new Set(vet_specialties)];
            
            const vet_reasons = [];
            vet_reasons.push(`${rating}/5 stars from ${reviewCount} reviews`);
            vet_reasons.push(`${distance} miles from your location`);
            vet_reasons.push(reasons[Math.floor(Math.random() * reasons.length)]);

            let reviewText = reviewTexts[Math.floor(Math.random() * reviewTexts.length)];
            reviewText = reviewText.replace("{pet}", petType === "exotic" ? "exotic pet" : petType);
            
            const handles_exotic = petType === "exotic" || Math.random() > 0.7;
            
            recommendations.push({
                id: `mock-${i}`,
                name: `${cityName} ${name}`,
                rating: parseFloat(rating),
                review_count: reviewCount,
                price: price,
                phone: `(${Math.floor(Math.random() * 900) + 100}) ${Math.floor(Math.random() * 900) + 100}-${Math.floor(Math.random() * 9000) + 1000}`,
                address: `${Math.floor(Math.random() * 9000) + 1000} ${["Main St", "Oak Ave", "Park Rd", "Maple Dr", "Cedar Ln"][Math.floor(Math.random() * 5)]}, ${cityName}`,
                coordinates: {
                    latitude: 37.7749 + (Math.random() - 0.5) * 0.1,
                    longitude: -122.4194 + (Math.random() - 0.5) * 0.1
                },
                image_url: "",
                url: `https://example.com/vet-${i}`,
                categories: uniqueSpecialties,
                reviews: [
                    {
                        id: `mock-review-${i}`,
                        rating: parseFloat(rating),
                        text: reviewText,
                        time_created: new Date().toISOString(),
                        user: { name: `LocalPetOwner${Math.floor(Math.random() * 1000)}` }
                    }
                ],
                distance: parseFloat(distance),
                handles_exotic: handles_exotic,
                source: "demo",
                recommendation_reasons: vet_reasons
            });
        }
        
        return {
            recommendations: recommendations,
            count: recommendations.length,
            query: {
                location: location,
                pet_type: petType
            },
            data_sources: ["demo"],
            timestamp: new Date().toISOString()
        };
    }
});