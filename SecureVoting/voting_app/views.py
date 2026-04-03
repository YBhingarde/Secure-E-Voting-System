from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .forms import RegisterForm
from .models import VoterProfile, Candidate, Vote
import base64, io, numpy as np, cv2, random
from django.core.files.base import ContentFile
from django.conf import settings
from PIL import Image
import imagehash
from django.core.mail import send_mail
from django.db.models import Count

def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user = VoterProfile.objects.get(username=username, password=password)
            otp = str(random.randint(100000, 999999))
            request.session['otp'] = otp
            request.session['temp_username'] = user.username
            
            try:
                send_mail(
                    'Secure E-Voting System - Login OTP',
                    f'Hello {user.first_name},\n\nYour OTP for E-Voting login is: {otp}\nDo not share this with anyone.',
                    settings.EMAIL_HOST_USER,
                    [user.email],
                    fail_silently=False,
                )
                return redirect('verify_otp')
            except Exception as e:
                error = "Failed to send OTP email. Please check your internet or email settings."
        except VoterProfile.DoesNotExist:
            error = "Invalid username or password"
    return render(request, 'login.html', {'error': error})

def verify_otp(request):
    error = None
    success = request.GET.get('success')  # Resend 
    
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        saved_otp = request.session.get('otp')
        
        if entered_otp and entered_otp == saved_otp:
            request.session['username'] = request.session.get('temp_username')
            
            if 'otp' in request.session: del request.session['otp']
            if 'temp_username' in request.session: del request.session['temp_username']
            return redirect('dashboard')
        else:
            error = "Invalid OTP! Please try again."
            
    return render(request, 'verify_otp.html', {'error': error, 'success': success})

#  (Resend )
def resend_otp(request):
    temp_username = request.session.get('temp_username')
    if not temp_username:
        return redirect('login')

    try:
        user = VoterProfile.objects.get(username=temp_username)
        
        new_otp = str(random.randint(100000, 999999))
        request.session['otp'] = new_otp
        
        
        send_mail(
            'Secure E-Voting System - Resend OTP',
            f'Hello {user.first_name},\n\nYour NEW OTP for E-Voting login is: {new_otp}\nDo not share this with anyone.',
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )
        # \success \
        from django.urls import reverse
        return redirect(reverse('verify_otp') + '?success=A new OTP has been sent to your email!')
    
    except Exception as e:
        from django.urls import reverse
        return redirect(reverse('verify_otp') + '?error=Failed to resend OTP. Try again.')

def get_logged_in_user(request):
    uname = request.session.get('username')
    if not uname: return None
    try: return VoterProfile.objects.get(username=uname)
    except VoterProfile.DoesNotExist: return None

def dashboard(request):
    user = get_logged_in_user(request)
    if not user: return redirect('login')
    return render(request, 'dashboard.html', {'user': user})

def candidates_list(request):
    user = get_logged_in_user(request)
    if not user: return redirect('login')
    candidates = Candidate.objects.all()
    return render(request, 'candidates_list.html', {'user': user, 'candidates': candidates})

def vote_verify(request, candidate_id):
    user = get_logged_in_user(request)
    if not user: return redirect('login')

    if Vote.objects.filter(user=user).exists():
        return redirect('vote_thanks')

    candidate = get_object_or_404(Candidate, id=candidate_id)

    if request.method == "POST":
        aadhaar_entered = (request.POST.get("aadhaar") or "").strip()
        phone_entered = (request.POST.get("phone") or "").strip()
        photo_data = request.POST.get("photoData")
        errors = []

        if Vote.objects.filter(aadhaar_entered=aadhaar_entered).exists():
            errors.append("This Aadhaar Number has already been used to vote!")
        if not (aadhaar_entered.isdigit() and len(aadhaar_entered) == 12):
            errors.append("Enter a valid 12-digit Aadhaar number.")
        if phone_entered != user.phone_number:
            errors.append("Phone number does not match your registered number.")
        if not photo_data:
            errors.append("Please capture your live photo before submitting.")

        if errors:
            return render(request, "voting_page.html", {"user": user, "candidate": candidate, "errors": errors})

        try:
            header, b64 = photo_data.split(";base64,")
            raw = base64.b64decode(b64)
            image_file = ContentFile(raw, name=f"{user.username}_vote.png")
        except Exception:
            return render(request, "voting_page.html", {"user": user, "candidate": candidate, "errors": ["Could not process image."]})

        # SMART OPENCV FACE CROP + PHASH LOGIC 
        
        try:
            np_arr = np.frombuffer(raw, np.uint8)
            img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            
            cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
            
            if len(faces) == 0:
                return render(request, "voting_page.html", {"user": user, "candidate": candidate, "errors": ["No face detected! Please look at the camera clearly."]})

            x, y, w, h = max(faces, key=lambda r: r[2] * r[3])
            face_bgr = img_bgr[y:y+h, x:x+w]
            face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
            
            face_img = Image.fromarray(face_rgb)
            ph = imagehash.phash(face_img, hash_size=16)
            ph_hex = str(ph)
            
            THRESHOLD = 35  # 30 if not recognizing face easily
            
            for v in Vote.objects.exclude(face_phash__isnull=True).exclude(face_phash__exact=""):
                try:
                    stored_hash = imagehash.hex_to_hash(v.face_phash)
                    if ph - stored_hash <= THRESHOLD:
                        return render(request, "voting_page.html", {"user": user, "candidate": candidate, "errors": ["Transaction Blocked: Duplicate face detected!"]})
                except Exception: 
                    continue
                    
        except Exception as e:
            return render(request, "voting_page.html", {"user": user, "candidate": candidate, "errors": ["Face processing error occurred. Try again."]})
        
        #  LOGIC ENDS HERE 🚀

        Vote.objects.create(
            user=user, 
            candidate=candidate, 
            aadhaar_entered=aadhaar_entered,
            phone_confirmed=phone_entered, 
            photo=image_file, 
            face_phash=ph_hex  
        )
        user.has_voted = True
        user.save()
        return redirect("vote_thanks")

    return render(request, "voting_page.html", {"user": user, "candidate": candidate})


def vote_thanks(request):
    user = get_logged_in_user(request)
    if not user: return redirect('login')
    return render(request, 'thank_you.html', {'user': user})

def how_it_works(request):
    return render(request, 'how_it_works.html')

def live_results(request):
    # total vote calculate
    total_votes = Vote.objects.count()
    
    # per candidate total cal
    candidates = Candidate.objects.annotate(votes=Count('vote')).order_by('-votes')
    
    # (Percentage)
    candidate_data = []
    for c in candidates:
        percentage = (c.votes / total_votes * 100) if total_votes > 0 else 0
        candidate_data.append({
            'name': c.name,
            'party': c.party,
            'votes': c.votes,
            'percentage': round(percentage, 1)
        })
        
    return render(request, 'live_results.html', {
        'candidate_data': candidate_data, 
        'total_votes': total_votes
    })