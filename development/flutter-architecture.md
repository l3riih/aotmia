# Arquitectura Flutter - Atomia

## Estructura del Proyecto Flutter

### Organización de Carpetas
```
lib/
├── core/
│   ├── constants/         # Constantes de la app
│   ├── errors/           # Manejo de errores
│   ├── network/          # Cliente HTTP y configuración
│   ├── routes/           # Definición de rutas
│   ├── theme/            # Temas y estilos
│   └── utils/            # Utilidades generales
├── data/
│   ├── datasources/      # Fuentes de datos (remote/local)
│   ├── models/           # Modelos de datos
│   └── repositories/     # Implementación de repositorios
├── domain/
│   ├── entities/         # Entidades de negocio
│   ├── repositories/     # Contratos de repositorios
│   └── usecases/         # Casos de uso
├── presentation/
│   ├── blocs/           # BLoCs globales
│   ├── pages/           # Páginas principales
│   ├── widgets/         # Widgets reutilizables
│   └── features/        # Features modulares
│       ├── onboarding/
│       ├── study_session/
│       ├── progress/
│       ├── atomization/
│       └── gamification/
└── main.dart            # Punto de entrada
```

## Arquitectura Clean + BLoC

### Capas de la Arquitectura

#### 1. Domain Layer (Capa de Dominio)
```dart
// domain/entities/learning_atom.dart
class LearningAtom {
  final String id;
  final String title;
  final String content;
  final String summary;
  final List<String> keywords;
  final List<String> learningObjectives;
  final List<String> prerequisites;
  final DifficultyLevel difficulty;
  final AtomType type;
  
  const LearningAtom({
    required this.id,
    required this.title,
    required this.content,
    required this.summary,
    required this.keywords,
    required this.learningObjectives,
    required this.prerequisites,
    required this.difficulty,
    required this.type,
  });
}

// domain/repositories/learning_repository.dart
abstract class LearningRepository {
  Future<Either<Failure, List<LearningAtom>>> getAtoms();
  Future<Either<Failure, LearningAtom>> getNextAtom(String userId);
  Future<Either<Failure, void>> submitAnswer(Answer answer);
  Future<Either<Failure, StudyPlan>> getStudyPlan(String userId);
}

// domain/usecases/get_next_atom.dart
class GetNextAtomUseCase {
  final LearningRepository repository;
  
  GetNextAtomUseCase(this.repository);
  
  Future<Either<Failure, LearningAtom>> call(String userId) {
    return repository.getNextAtom(userId);
  }
}
```

#### 2. Data Layer (Capa de Datos)
```dart
// data/models/learning_atom_model.dart
class LearningAtomModel extends LearningAtom {
  const LearningAtomModel({
    required super.id,
    required super.title,
    required super.content,
    required super.summary,
    required super.keywords,
    required super.learningObjectives,
    required super.prerequisites,
    required super.difficulty,
    required super.type,
  });
  
  factory LearningAtomModel.fromJson(Map<String, dynamic> json) {
    return LearningAtomModel(
      id: json['id'],
      title: json['title'],
      content: json['content'],
      summary: json['summary'],
      keywords: List<String>.from(json['keywords']),
      learningObjectives: List<String>.from(json['learning_objectives']),
      prerequisites: List<String>.from(json['prerequisites']),
      difficulty: DifficultyLevel.fromString(json['difficulty_level']),
      type: AtomType.fromString(json['type']),
    );
  }
  
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'content': content,
      'summary': summary,
      'keywords': keywords,
      'learning_objectives': learningObjectives,
      'prerequisites': prerequisites,
      'difficulty_level': difficulty.toString(),
      'type': type.toString(),
    };
  }
}

// data/datasources/learning_remote_datasource.dart
abstract class LearningRemoteDataSource {
  Future<List<LearningAtomModel>> getAtoms();
  Future<LearningAtomModel> getNextAtom(String userId);
  Future<void> submitAnswer(AnswerModel answer);
}

class LearningRemoteDataSourceImpl implements LearningRemoteDataSource {
  final Dio dio;
  final String baseUrl;
  
  LearningRemoteDataSourceImpl({
    required this.dio,
    required this.baseUrl,
  });
  
  @override
  Future<LearningAtomModel> getNextAtom(String userId) async {
    try {
      final response = await dio.get(
        '$baseUrl/api/v1/atoms/next',
        queryParameters: {'user_id': userId},
      );
      
      return LearningAtomModel.fromJson(response.data);
    } on DioError catch (e) {
      throw ServerException(e.message ?? 'Server error');
    }
  }
}
```

#### 3. Presentation Layer (Capa de Presentación)
```dart
// presentation/features/study_session/bloc/study_session_bloc.dart
class StudySessionBloc extends Bloc<StudySessionEvent, StudySessionState> {
  final GetNextAtomUseCase getNextAtom;
  final SubmitAnswerUseCase submitAnswer;
  final GenerateQuestionsUseCase generateQuestions;
  
  StudySessionBloc({
    required this.getNextAtom,
    required this.submitAnswer,
    required this.generateQuestions,
  }) : super(StudySessionInitial()) {
    on<LoadNextAtom>(_onLoadNextAtom);
    on<SubmitAnswer>(_onSubmitAnswer);
    on<GenerateQuestions>(_onGenerateQuestions);
  }
  
  Future<void> _onLoadNextAtom(
    LoadNextAtom event,
    Emitter<StudySessionState> emit,
  ) async {
    emit(StudySessionLoading());
    
    final result = await getNextAtom(event.userId);
    
    result.fold(
      (failure) => emit(StudySessionError(failure.message)),
      (atom) => emit(StudySessionAtomLoaded(atom)),
    );
  }
}

// presentation/features/study_session/pages/study_session_page.dart
class StudySessionPage extends StatelessWidget {
  const StudySessionPage({Key? key}) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (context) => getIt<StudySessionBloc>()
        ..add(LoadNextAtom(userId: context.read<AuthBloc>().state.user.id)),
      child: Scaffold(
        body: BlocBuilder<StudySessionBloc, StudySessionState>(
          builder: (context, state) {
            if (state is StudySessionLoading) {
              return const LoadingWidget();
            } else if (state is StudySessionAtomLoaded) {
              return AtomContentWidget(atom: state.atom);
            } else if (state is StudySessionQuestionReady) {
              return QuestionWidget(
                question: state.question,
                onAnswer: (answer) {
                  context.read<StudySessionBloc>().add(
                    SubmitAnswer(answer: answer),
                  );
                },
              );
            } else if (state is StudySessionError) {
              return ErrorWidget(message: state.message);
            }
            return const SizedBox.shrink();
          },
        ),
      ),
    );
  }
}
```

## Componentes UI Reutilizables

### Sistema de Diseño
```dart
// presentation/widgets/atoms/primary_button.dart
class PrimaryButton extends StatelessWidget {
  final String text;
  final VoidCallback onPressed;
  final bool isLoading;
  
  const PrimaryButton({
    Key? key,
    required this.text,
    required this.onPressed,
    this.isLoading = false,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: isLoading ? null : onPressed,
      style: ElevatedButton.styleFrom(
        backgroundColor: Theme.of(context).primaryColor,
        padding: const EdgeInsets.symmetric(
          horizontal: 32,
          vertical: 16,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
      child: isLoading
          ? const CircularProgressIndicator(color: Colors.white)
          : Text(
              text,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
    );
  }
}

// presentation/widgets/molecules/question_card.dart
class QuestionCard extends StatelessWidget {
  final Question question;
  final Function(String) onAnswerSelected;
  
  const QuestionCard({
    Key? key,
    required this.question,
    required this.onAnswerSelected,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              question.text,
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 16),
            if (question is MultipleChoiceQuestion)
              ...question.options.map(
                (option) => OptionTile(
                  option: option,
                  onTap: () => onAnswerSelected(option.id),
                ),
              ),
            if (question is TrueFalseQuestion)
              Row(
                children: [
                  Expanded(
                    child: PrimaryButton(
                      text: 'Verdadero',
                      onPressed: () => onAnswerSelected('true'),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: PrimaryButton(
                      text: 'Falso',
                      onPressed: () => onAnswerSelected('false'),
                    ),
                  ),
                ],
              ),
          ],
        ),
      ),
    );
  }
}
```

## Gestión de Estado Avanzada

### BLoC con Cubits para Estado Simple
```dart
// presentation/features/theme/cubit/theme_cubit.dart
class ThemeCubit extends Cubit<ThemeMode> {
  ThemeCubit() : super(ThemeMode.system);
  
  void setTheme(ThemeMode mode) {
    emit(mode);
    // Persistir preferencia
    _saveThemePreference(mode);
  }
  
  Future<void> loadTheme() async {
    final mode = await _loadThemePreference();
    emit(mode);
  }
}

// presentation/features/connectivity/cubit/connectivity_cubit.dart
class ConnectivityCubit extends Cubit<ConnectivityStatus> {
  final Connectivity connectivity;
  StreamSubscription? _subscription;
  
  ConnectivityCubit({required this.connectivity}) 
    : super(ConnectivityStatus.unknown) {
    _checkConnectivity();
    _subscription = connectivity.onConnectivityChanged.listen(_updateStatus);
  }
  
  void _updateStatus(ConnectivityResult result) {
    if (result == ConnectivityResult.none) {
      emit(ConnectivityStatus.offline);
    } else {
      emit(ConnectivityStatus.online);
    }
  }
  
  @override
  Future<void> close() {
    _subscription?.cancel();
    return super.close();
  }
}
```

## Sincronización Offline

### Implementación de Cache Local
```dart
// data/datasources/learning_local_datasource.dart
abstract class LearningLocalDataSource {
  Future<void> cacheAtoms(List<LearningAtomModel> atoms);
  Future<List<LearningAtomModel>> getCachedAtoms();
  Future<void> cacheProgress(ProgressModel progress);
  Future<ProgressModel?> getCachedProgress();
  Future<void> addPendingAnswer(AnswerModel answer);
  Future<List<AnswerModel>> getPendingAnswers();
  Future<void> clearPendingAnswers();
}

class LearningLocalDataSourceImpl implements LearningLocalDataSource {
  final HiveInterface hive;
  
  static const String atomsBoxName = 'atoms';
  static const String progressBoxName = 'progress';
  static const String pendingAnswersBoxName = 'pending_answers';
  
  @override
  Future<void> cacheAtoms(List<LearningAtomModel> atoms) async {
    final box = await hive.openBox<Map>(atomsBoxName);
    final atomsMap = {
      for (var atom in atoms) atom.id: atom.toJson()
    };
    await box.putAll(atomsMap);
  }
  
  @override
  Future<void> addPendingAnswer(AnswerModel answer) async {
    final box = await hive.openBox<Map>(pendingAnswersBoxName);
    await box.add(answer.toJson());
  }
}

// data/repositories/learning_repository_impl.dart
class LearningRepositoryImpl implements LearningRepository {
  final LearningRemoteDataSource remoteDataSource;
  final LearningLocalDataSource localDataSource;
  final NetworkInfo networkInfo;
  
  @override
  Future<Either<Failure, LearningAtom>> getNextAtom(String userId) async {
    if (await networkInfo.isConnected) {
      try {
        final atom = await remoteDataSource.getNextAtom(userId);
        // Cache para uso offline
        await localDataSource.cacheAtoms([atom]);
        return Right(atom);
      } on ServerException {
        return Left(ServerFailure());
      }
    } else {
      // Modo offline: obtener del cache
      try {
        final atoms = await localDataSource.getCachedAtoms();
        if (atoms.isNotEmpty) {
          // Lógica simple para siguiente átomo offline
          return Right(atoms.first);
        } else {
          return Left(CacheFailure());
        }
      } on CacheException {
        return Left(CacheFailure());
      }
    }
  }
}
```

## Animaciones y Transiciones

### Animaciones Fluidas
```dart
// presentation/widgets/animations/fade_slide_transition.dart
class FadeSlideTransition extends StatelessWidget {
  final Widget child;
  final Animation<double> animation;
  final Offset beginOffset;
  
  const FadeSlideTransition({
    Key? key,
    required this.child,
    required this.animation,
    this.beginOffset = const Offset(0, 0.3),
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: animation,
      builder: (context, child) {
        return FadeTransition(
          opacity: animation,
          child: SlideTransition(
            position: Tween<Offset>(
              begin: beginOffset,
              end: Offset.zero,
            ).animate(CurvedAnimation(
              parent: animation,
              curve: Curves.easeOutCubic,
            )),
            child: child,
          ),
        );
      },
      child: child,
    );
  }
}

// presentation/widgets/animations/progress_animation.dart
class AnimatedProgressBar extends StatelessWidget {
  final double progress;
  final Duration duration;
  
  const AnimatedProgressBar({
    Key? key,
    required this.progress,
    this.duration = const Duration(milliseconds: 800),
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: progress),
      duration: duration,
      curve: Curves.easeInOut,
      builder: (context, value, child) {
        return CustomPaint(
          size: const Size(double.infinity, 8),
          painter: ProgressPainter(
            progress: value,
            color: Theme.of(context).primaryColor,
          ),
        );
      },
    );
  }
}
```

## Gamificación UI

### Componentes de Gamificación
```dart
// presentation/features/gamification/widgets/achievement_popup.dart
class AchievementPopup extends StatefulWidget {
  final Achievement achievement;
  final VoidCallback onDismiss;
  
  const AchievementPopup({
    Key? key,
    required this.achievement,
    required this.onDismiss,
  }) : super(key: key);
  
  @override
  State<AchievementPopup> createState() => _AchievementPopupState();
}

class _AchievementPopupState extends State<AchievementPopup>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;
  late Animation<double> _fadeAnimation;
  
  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 600),
      vsync: this,
    );
    
    _scaleAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.elasticOut,
    ));
    
    _fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: const Interval(0.0, 0.5),
    ));
    
    _controller.forward();
    
    // Auto dismiss después de 3 segundos
    Future.delayed(const Duration(seconds: 3), () {
      if (mounted) {
        _controller.reverse().then((_) => widget.onDismiss());
      }
    });
  }
  
  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Opacity(
          opacity: _fadeAnimation.value,
          child: Transform.scale(
            scale: _scaleAnimation.value,
            child: Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.2),
                    blurRadius: 20,
                    offset: const Offset(0, 10),
                  ),
                ],
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.emoji_events,
                    size: 64,
                    color: Colors.amber,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    '¡${widget.achievement.title}!',
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    widget.achievement.description,
                    style: Theme.of(context).textTheme.bodyMedium,
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}
```

## Testing en Flutter

### Unit Tests
```dart
// test/domain/usecases/get_next_atom_test.dart
void main() {
  late GetNextAtomUseCase useCase;
  late MockLearningRepository mockRepository;
  
  setUp(() {
    mockRepository = MockLearningRepository();
    useCase = GetNextAtomUseCase(mockRepository);
  });
  
  test('should get next atom from repository', () async {
    // Arrange
    const userId = 'test_user';
    final atom = LearningAtom(
      id: 'atom_1',
      title: 'Test Atom',
      content: 'Test content',
      // ... otros campos
    );
    
    when(() => mockRepository.getNextAtom(userId))
        .thenAnswer((_) async => Right(atom));
    
    // Act
    final result = await useCase(userId);
    
    // Assert
    expect(result, Right(atom));
    verify(() => mockRepository.getNextAtom(userId)).called(1);
  });
}
```

### Widget Tests
```dart
// test/presentation/widgets/question_card_test.dart
void main() {
  testWidgets('QuestionCard displays question text', (tester) async {
    // Arrange
    final question = MultipleChoiceQuestion(
      id: 'q1',
      text: 'What is Flutter?',
      options: [
        Option(id: 'o1', text: 'A framework'),
        Option(id: 'o2', text: 'A language'),
      ],
    );
    
    // Act
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: QuestionCard(
            question: question,
            onAnswerSelected: (_) {},
          ),
        ),
      ),
    );
    
    // Assert
    expect(find.text('What is Flutter?'), findsOneWidget);
    expect(find.text('A framework'), findsOneWidget);
    expect(find.text('A language'), findsOneWidget);
  });
}
```

### Integration Tests
```dart
// integration_test/study_session_test.dart
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  
  testWidgets('Complete study session flow', (tester) async {
    // Inicializar app
    await tester.pumpWidget(const AtomiaApp());
    
    // Login
    await tester.enterText(find.byKey(const Key('email_field')), 'test@test.com');
    await tester.enterText(find.byKey(const Key('password_field')), 'password');
    await tester.tap(find.byKey(const Key('login_button')));
    await tester.pumpAndSettle();
    
    // Navegar a sesión de estudio
    await tester.tap(find.text('Comenzar Estudio'));
    await tester.pumpAndSettle();
    
    // Verificar que se carga un átomo
    expect(find.byType(AtomContentWidget), findsOneWidget);
    
    // Responder pregunta
    await tester.tap(find.text('Siguiente'));
    await tester.pumpAndSettle();
    
    expect(find.byType(QuestionCard), findsOneWidget);
    
    // Seleccionar respuesta
    await tester.tap(find.text('Opción A'));
    await tester.pumpAndSettle();
    
    // Verificar feedback
    expect(find.text('¡Correcto!'), findsOneWidget);
  });
}
```

## Performance Optimization

### Lazy Loading y Pagination
```dart
// presentation/features/atom_list/widgets/atom_list_view.dart
class AtomListView extends StatefulWidget {
  @override
  State<AtomListView> createState() => _AtomListViewState();
}

class _AtomListViewState extends State<AtomListView> {
  final ScrollController _scrollController = ScrollController();
  
  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
  }
  
  void _onScroll() {
    if (_isBottom) {
      context.read<AtomListBloc>().add(LoadMoreAtoms());
    }
  }
  
  bool get _isBottom {
    if (!_scrollController.hasClients) return false;
    final maxScroll = _scrollController.position.maxScrollExtent;
    final currentScroll = _scrollController.offset;
    return currentScroll >= (maxScroll * 0.9);
  }
  
  @override
  Widget build(BuildContext context) {
    return BlocBuilder<AtomListBloc, AtomListState>(
      builder: (context, state) {
        if (state is AtomListLoaded) {
          return ListView.builder(
            controller: _scrollController,
            itemCount: state.hasReachedMax
                ? state.atoms.length
                : state.atoms.length + 1,
            itemBuilder: (context, index) {
              if (index >= state.atoms.length) {
                return const Center(
                  child: CircularProgressIndicator(),
                );
              }
              return AtomTile(atom: state.atoms[index]);
            },
          );
        }
        return const LoadingWidget();
      },
    );
  }
}
``` 